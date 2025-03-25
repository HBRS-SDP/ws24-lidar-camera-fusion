## Build the docker file 
This docker file is built upon the ros noetic (ros1) desktop full version:
* installs the required packages (ros packages, packages required by r3live or livox lidar driver).
* installs the python requirements 
* clones the r3live,livox lidar driver repositories and install them  
* build the ros workspace
* copy the ros bags to the docker images (better to mount a disk)
* call an entrypoint, this entrypoint sources the catkin workspace and runs two tmux sessions. one init the ros core and one run jupyter lab to have gui interface.

## Building steps:
* make sure to have the ros bags in the same directory with the docker file 

```bash
cd docker_file
```

```bash
docker build -t r3live_wrapper .
```

* to run a docker container based on this image:
```bash
docker run -it --rm --name r3live-wrapper \
    -p 11311:11311 -p 8888:8888 \
    -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
    --net=host --runtime=nvidia \
    r3live_wrapper:latest /bin/bash 
```
* to execut the running container in new terminal :
```bash
docker exec -it r3live-wrapper /bin/bash
```

* enable docker gui :
```bash
sudo xhost +local:docker
```

