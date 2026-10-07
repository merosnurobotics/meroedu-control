# 수업 전에 준비하는 Jetson

작성자: 조연우 · yencho929@snu.ac.kr

실습 기준은 Jetson Orin Nano 8GB, JetPack 6 계열의 Ubuntu 22.04, ROS 2 Humble, 시스템 Python 3.10입니다. 사용 이력이 있는 구성을 유지합니다. JetPack의 특정 minor 버전은 기록으로 확정되지 않아 고정하지 않습니다. 카메라·CUDA·학습 프레임워크는 이 제어 실습에 필요하지 않습니다.

1. Jetson에 모델에 맞는 JetPack 6 이미지를 설치하고 최초 부팅·네트워크·사용자 계정을 준비합니다. [NVIDIA JetPack 안내](https://developer.nvidia.com/embedded/jetpack).
2. [ROS 2 Humble Ubuntu deb 설치 안내](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html)를 따라 Ubuntu 22.04에 `ros-humble-ros-base`를 설치합니다. 다른 Ubuntu/ROS 조합에 Humble 명령을 그대로 적용하지 않습니다.
3. 아래 의존성과 USB 접근 권한을 준비합니다. OS 설치·ROS 설치는 수업 전에 끝내고, 학생은 아래 점검부터 시작합니다.

```bash
sudo apt update
sudo apt install python3-serial ros-humble-geometry-msgs ros-humble-std-msgs
sudo usermod -aG dialout "$USER"
# 로그아웃 후 다시 로그인해야 현재 세션에 dialout 그룹이 적용됩니다.
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42
/usr/bin/python3 --version
/usr/bin/python3 -c 'import serial, rclpy; from geometry_msgs.msg import Twist; from std_msgs.msg import String; print("ready")'
```

모든 ROS 터미널에서 같은 setup과 ROS_DOMAIN_ID를 사용합니다. 여러 팀이 함께 실습하면 팀마다 0~101 안의 서로 다른 번호를 정합니다. Python venv/Conda 대신 `/usr/bin/python3`로 apt 설치된 ROS 모듈을 사용합니다.

## USB 장치 확인

```bash
ls -l /dev/serial/by-id/
groups
# 포트를 골라 장치명이 실제로 무엇인지 확인합니다.
readlink -f /dev/serial/by-id/여기에는-실제-장치명
```

Arduino와 OpenRB를 하나씩 연결해 이름을 구분합니다. `/dev/ttyACM0`은 연결 순서에 따라 바뀝니다. 실습 명령의 `PORT`는 실제 `/dev/serial/by-id/...` 경로로 바꾸세요. Serial monitor·Wizard·터미널 프로그램·ROS bridge 중 하나만 해당 포트를 엽니다. 업로드 전에는 bridge를 종료합니다.

Jetson USB는 명령 통신용입니다. Motor driver와 DYNAMIXEL 전원은 해당 모델 규격에 맞게 별도로 연결합니다. 불안정한 USB 연결에는 케이블·전원·전원이 공급되는 USB hub를 점검하세요. 임의의 장치에 같은 전압을 공급하지 않습니다.

## 수업 전 점검

저장소 루트에서 `bash setup/check_jetson.sh`로 OS·Python·ROS·권한·USB 목록을 읽기 전용으로 확인합니다. 이 스크립트는 설치·펌웨어 업로드·모터 동작을 하지 않습니다. 실제 동작은 각 강의의 별도 절차에서 실행합니다.
