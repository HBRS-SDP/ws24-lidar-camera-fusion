#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class ImageFormatConverterNode:
    def __init__(self):
        # Initialize CV Bridge
        self.bridge = CvBridge()

        # Subscribe to the problematic image topic
        self.sub = rospy.Subscriber('/dji_osdk_ros/main_camera_images', Image, self.image_callback)

        # Publisher for the corrected image topic
        self.pub = rospy.Publisher('/camera/image_color', Image, queue_size=10)

        # Desired format (based on /camera/image_color)
        self.desired_encoding = 'rgb8'
        self.desired_width = 640 
        self.desired_height = 512 

    def image_callback(self, msg):
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
            self.pub.publish(corrected_msg)
        except Exception as e:
            rospy.logerr(f"Error processing image: {e}")

if __name__ == "__main__":
    # Initialize ROS node
    rospy.init_node('image_transfer_node')

    # Create an instance of the ImageFormatConverterNode class
    converter = ImageFormatConverterNode()

    # Keep the node running
    rospy.spin()