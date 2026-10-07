# MERO 교육 · Control / ROS 하드웨어

시리즈 안에 여러 강의를 순서대로 추가하는 실습 저장소입니다. 웹 분류에서 PID/OpenRB 기본은 Control, ROS로 hardware 제어하는 자료는 ROS에 모읍니다. 코드 폴더는 기존 시리즈 경로를 유지합니다. 각 강의는 독립 실행하고, 필요한 코드와 환경 설정만 담습니다. 데이터·학습 가중치·개인키·원본 프로젝트 로그는 포함하지 않습니다.

| 순서 | 강의 | 실습 폴더 | 설명 자료 |
| --- | --- | --- | --- |
| 01 | PID control | [lessons/01-pid](lessons/01-pid/README.md) | [MERO 교육 자료](https://mero-website-one.vercel.app/education/control/pid-control) |
| 02 | ROS로 encoder motor 제어하기 | [lessons/02-ros-arduino-motor](lessons/02-ros-arduino-motor/README.md) | [MERO 교육 자료](https://mero-website-one.vercel.app/education/ros/arduino-motor) |
| 03 | OpenRB + DYNAMIXEL 기본 사용 | [lessons/03-openrb-dynamixel](lessons/03-openrb-dynamixel/README.md) | [MERO 교육 자료](https://mero-website-one.vercel.app/education/control/openrb-dynamixel) |
| 04 | ROS 2 토픽으로 DYNAMIXEL 제어 | [lessons/04-ros2-dynamixel](lessons/04-ros2-dynamixel/README.md) | [MERO 교육 자료](https://mero-website-one.vercel.app/education/ros/dynamixel) |

## 시작하기

```bash
git clone https://github.com/merosnurobotics/meroedu-control.git
cd meroedu-control/lessons/01-pid
```

강의 폴더의 README를 따라갑니다. 웹사이트 강의와 이 코드 저장소는 모두 공개입니다.

## 새 강의 추가

`lessons/02-주제`, `lessons/03-주제`처럼 별도 폴더에 README·필요 코드·환경 정보를 작성하고 이 목록에 추가합니다. 기존 강의의 환경과 실행 경로를 바꾸지 않습니다. 미래 강의용 빈 폴더는 만들지 않습니다.

하드웨어 실습 전에 [Jetson 공통 셋업](setup/JETSON_SETUP.md)을 완료하세요. 03은 OpenRB/SAMD + Dynamixel2Arduino, 04는 ROS 2 Humble bridge를 추가합니다.

01은 Python 3.10 표준 라이브러리, 02는 ROS 2/rclpy/pySerial과 Arduino UNO AVR 환경을 사용합니다. 각 회차 README에서 준비합니다. [CONTRIBUTING](CONTRIBUTING.md)
