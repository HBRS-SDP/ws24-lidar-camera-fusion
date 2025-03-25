#!/bin/bash
set -e

# Source ROS and workspace
source /opt/ros/noetic/setup.bash
[ -f /catkin_ws/devel/setup.bash ] && source /catkin_ws/devel/setup.bash

# Add sourcing commands to .bashrc for all shell sessions
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
echo "source /catkin_ws/devel/setup.bash" >> ~/.bashrc

echo "[ENTRYPOINT] Sourcing done."

# Start roscore in a tmux session (only if not already running)
if ! tmux has-session -t ros 2>/dev/null; then
    echo "[ENTRYPOINT] Starting roscore in tmux..."
    tmux new-session -d -s ros "roscore"
fi

# Start Jupyter Lab in a separate tmux session
if ! tmux has-session -t jupyter 2>/dev/null; then
    echo "[ENTRYPOINT] Starting Jupyter Lab in tmux..."
    tmux new-session -d -s jupyter "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root"
fi

# Then run passed command (like bash or a launch file)
exec "$@"
