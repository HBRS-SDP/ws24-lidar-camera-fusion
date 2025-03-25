import rospy
import cv2
import rosbag
import threading
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, PointCloud2, Imu
from sensor_msgs import point_cloud2 as pc2
from livox_ros_driver.msg import CustomMsg, CustomPoint

class BagConverterNode:
    def __init__(self, output_bag_path):
        # Initialize CV Bridge
        self.bridge = CvBridge()

        # Desired format for image conversion
        self.desired_encoding = 'rgb8'
        self.desired_width = 640  # Replace with the actual width of /camera/image_color
        self.desired_height = 512  # Replace with the actual height of /camera/image_color

        # Open the output bag for writing
        self.output_bag = rosbag.Bag(output_bag_path, 'w')

        # Mutex for thread safety
        self.mutex = threading.Lock()

        # Flag to indicate if the node is shutting down
        self.shutting_down = False

        # Publishers for the target topics
        self.image_pub = rospy.Publisher('/camera/image_color', Image, queue_size=10)
        self.imu_pub = rospy.Publisher('/livox/imu', Imu, queue_size=10)
        self.pointcloud_pub = rospy.Publisher('/livox/lidar', CustomMsg, queue_size=10)

        # Subscribers for the original topics
        self.image_sub = rospy.Subscriber('/dji_osdk_ros/main_camera_images', Image, self.image_callback)
        self.imu_sub = rospy.Subscriber('/dji_osdk_ros/imu', Imu, self.imu_callback)
        self.pointcloud_sub = rospy.Subscriber('/velodyne_points', PointCloud2, self.pointcloud_callback)

        # Rate object to control callback execution
        self.rate = rospy.Rate(10)  # 10 Hz

    def image_callback(self, msg):
        """
        Callback for the /dji_osdk_ros/main_camera_images topic.
        """
        if self.shutting_down:
            return

        try:
            # Convert ROS Image message to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding=self.desired_encoding)

            # Resize the image to match the desired dimensions
            if cv_image.shape[0] != self.desired_height or cv_image.shape[1] != self.desired_width:
                cv_image = cv2.resize(cv_image, (self.desired_width, self.desired_height))

            # Convert back to ROS Image message
            corrected_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding=self.desired_encoding)
            corrected_msg.header = msg.header  # Preserve the original header

            # Publish the corrected image
            self.image_pub.publish(corrected_msg)

            # Write the corrected image to the output bag
            with self.mutex:
                if not self.shutting_down:
                    self.output_bag.write('/camera/image_color', corrected_msg, msg.header.stamp)
        except Exception as e:
            rospy.logerr(f"Error processing image: {e}")

    def imu_callback(self, msg):
        """
        Callback for the /dji_osdk_ros/imu topic.
        """
        if self.shutting_down:
            return

        try:
            # Publish the IMU message directly
            self.imu_pub.publish(msg)

            # Write the IMU message to the output bag
            with self.mutex:
                if not self.shutting_down:
                    self.output_bag.write('/livox/imu', msg, msg.header.stamp)
        except Exception as e:
            rospy.logerr(f"Error republishing IMU message: {e}")

    def pointcloud_callback(self, msg):
        """
        Callback for the /velodyne_points topic.
        """
        if self.shutting_down:
            return

        try:
            # Convert PointCloud2 to CustomMsg
            custom_msg = CustomMsg()
            custom_msg.header = msg.header  # Copy the header
            custom_msg.timebase = 0  # Set timebase (adjust as needed)
            custom_msg.point_num = 0  # Initialize point count

            # Convert the generator to a list to avoid dictionary modification during iteration
            points = list(pc2.read_points(msg, field_names=("x", "y", "z", "intensity"), skip_nans=True))

            # Iterate through the points
            for point in points:
                custom_point = CustomPoint()
                custom_point.x = point[0]
                custom_point.y = point[1]
                custom_point.z = point[2]
                custom_point.reflectivity = int(point[3])  # Use intensity as reflectivity
                custom_point.tag = 0  # Set tag (adjust as needed)
                custom_point.line = 0  # Set line (adjust as needed)

                # Add the point to the CustomMsg
                custom_msg.points.append(custom_point)
                custom_msg.point_num += 1

            # Publish the CustomMsg
            self.pointcloud_pub.publish(custom_msg)

            # Write the CustomMsg to the output bag
            with self.mutex:
                if not self.shutting_down:
                    self.output_bag.write('/livox/lidar', custom_msg, msg.header.stamp)
        except Exception as e:
            rospy.logerr(f"Error converting PointCloud2 to CustomMsg: {e}")

    def shutdown(self):
        """
        Close the output bag when the node is shut down.
        """
        with self.mutex:
            self.shutting_down = True
            self.output_bag.close()
            rospy.loginfo("Output bag closed.")

if __name__ == '__main__':
    try:
        # Initialize the ROS node
        rospy.init_node('bag_converter_node')

        # Specify the output bag path
        output_bag_path = '/ros_bags/output.bag'

        # Create an instance of the BagConverterNode
        node = BagConverterNode(output_bag_path)

        # Spin to keep the node running
        rospy.spin()

    except rospy.ROSInterruptException:
        pass
    finally:
        # Ensure the output bag is closed on shutdown
        node.shutdown()