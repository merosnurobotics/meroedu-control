#!/usr/bin/env bash
set -eu
. /etc/os-release
printf 'OS: %s\n' "$PRETTY_NAME"
/usr/bin/python3 --version
if [ -f /opt/ros/humble/setup.bash ]; then
  set +u
  . /opt/ros/humble/setup.bash
  set -u
  /usr/bin/python3 -c 'import serial, rclpy; from geometry_msgs.msg import Twist; from std_msgs.msg import String; print("ROS Humble + pySerial: ready")'
else
  printf 'ROS Humble setup not found\n'
  exit 1
fi
id -nG
if [ -d /dev/serial/by-id ]; then ls -l /dev/serial/by-id/; else printf 'No USB serial devices enumerated\n'; fi
