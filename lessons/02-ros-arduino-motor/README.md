# 02 · Jetson에서 ROS로 encoder motor 제어하기

작성자: 조연우 · yencho929@snu.ac.kr

수업 전에 [Jetson 공통 셋업](../../setup/JETSON_SETUP.md)을 완료합니다. Jetson Orin Nano 8GB / JetPack 6 / Ubuntu 22.04 / ROS 2 Humble / 시스템 Python 3.10 기준입니다.

ROS 2의 `/cmd_vel`에서 로봇 속도를 받아 USB serial로 Arduino에 전달합니다. Arduino는 메카넘 네 바퀴의 목표 속도를 구하고 encoder 측정과 PI + feedforward로 PWM을 보정합니다. Motor driver는 PWM/DIR 입력에 따라 외부 전원으로 모터를 구동합니다.

## 구성과 역할

```text
ROS publisher --/cmd_vel(Twist)--> Jetson bridge
Jetson --USB serial: m vx vy wz--> Arduino UNO R3
Arduino --PWM + DIR--> 2 × MDD10A --> 4 × encoder motor
Motor --encoder A/B--> Arduino --STATE line--> Jetson /motor/state
```

예제는 X 배열의 메카넘 4륜, Arduino UNO R3(ATmega328P), PWM/DIR 방식의 Cytron MDD10A 2개 기준입니다. `/cmd_vel`은 모터 PWM이 아니라 로봇 몸체의 목표 속도입니다. 바퀴 순서는 FL, FR, RL, RR이며 +x 앞, +y 왼쪽, +yaw 반시계 방향입니다. 차동 구동이나 다른 driver에는 바퀴 변환과 입출력 방식을 바꿔야 합니다.

| 파일 | 역할 |
| --- | --- |
| `bridge_node.py` | Twist 구독, 속도 제한, serial 송수신, 명령 timeout |
| `protocol.py` | 명령 문자열, 메카넘 바퀴 변환, STATE 해석 |
| `firmware/encoder_motor/encoder_motor.ino` | 명령 해석, encoder x4 측정, 20 ms 속도 PI, PWM/DIR, watchdog |

Position move, odometry/TF, gripper, reconnect 자동 동작은 이 실습의 기능에 포함하지 않습니다.

## 1. ROS 환경과 저장소

ROS 2가 설치된 Jetson 또는 Ubuntu 컴퓨터를 사용합니다. 명령 예시는 Ubuntu 22.04 / Humble / 시스템 Python 3.10입니다. OS와 배포판은 [ROS 설치 안내](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html)에 맞춥니다. 원격 작업은 [ssh jetson 자료](https://mero-website-one.vercel.app/education/development-setup/remote-work)를 참고합니다.

```bash
cd ~
git clone https://github.com/merosnurobotics/meroedu-control.git
cd meroedu-control/lessons/02-ros-arduino-motor
sudo apt install python3-serial
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42
/usr/bin/python3 -c "import rclpy, serial, geometry_msgs, std_msgs"
```

이미 clone했다면 저장소 루트에서 `git pull --ff-only` 후 02 폴더로 이동합니다. 아래 세 터미널 모두 setup을 source하고 같은 ROS_DOMAIN_ID를 사용합니다. 첫 실습은 같은 컴퓨터에서 실행합니다. Tailscale만으로 ROS discovery가 자동으로 연결되지는 않습니다. Jetson의 SSH 터미널 여러 개에서 실행해도 됩니다.

## 2. 모터 없이 먼저 확인

A — 기본값은 dry run. 실제 serial port를 열지 않습니다:

```bash
cd ~/meroedu-control/lessons/02-ros-arduino-motor
/usr/bin/python3 bridge_node.py
```

B — 10 Hz로 작은 전진 목표를 발행:

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.03, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}'
```

C — Arduino로 보낼 명령 확인:

```bash
ros2 topic echo /motor/serial_tx --once
```

내용이 `m 0.03000 0.00000 0.00000`이면 ROS의 linear.x가 serial의 vx로 연결된 것입니다. 이 토픽은 보낼 명령 문자열이며 실제 모터 동작이나 Arduino 수신 확인이 아닙니다. B를 Ctrl+C로 멈추면 약 0.5초 후 `stop`으로 바뀝니다. Arduino 연결 전에는 `/motor/state`에 실측 피드백이 나오지 않습니다.

## 3. Arduino와 driver 배선

이 표는 포함한 UNO sketch와 맞는 예시입니다. Motor driver의 M1/M2 채널 순서도 FL/FR/RL/RR에 맞춥니다. 바퀴/encoder 방향은 아래 polarity 설정으로 확인합니다.

| 바퀴 | DIR | PWM | Encoder A | Encoder B | Driver |
| --- | --- | --- | --- | --- | --- |
| FL 앞왼쪽 | D4 | D5 | D8 | D9 | #1 M1 |
| FR 앞오른쪽 | D7 | D6 | A0 | A1 | #1 M2 |
| RL 뒤왼쪽 | D2 | D3 | A2 | A3 | #2 M1 |
| RR 뒤오른쪽 | D12 | D10 | D11 | A5 | #2 M2 |

- Jetson↔Arduino는 USB. D0/D1은 USB serial을 위해 비워둡니다.
- Arduino PWM/DIR/GND를 driver 제어 입력에 연결합니다. Encoder A/B/VCC/GND는 encoder 사양의 전압과 출력 형태에 맞춥니다. 이 예제의 UNO 입력은 5 V 논리 기준이며 encoder 핀은 INPUT_PULLUP입니다.
- Motor 전원은 driver의 전원 입력에 따로 공급하고 driver 출력에 모터를 연결합니다. Arduino 5 V 핀으로 모터를 구동하지 않습니다. 신호 기준을 맞추도록 Arduino와 driver의 GND를 공유합니다.
- Jetson GPIO에 UNO의 5 V 신호를 직접 연결하지 않습니다. 이 흐름에서는 USB로만 통신합니다.

Motor/driver의 정격과 배선을 확인하고 물리 전원 차단 수단을 둡니다. 첫 회전 확인은 바퀴를 바닥에서 띄운 상태에서 작은 명령으로 진행합니다.

## 4. Firmware 설정과 업로드

`encoder_motor.ino`에서 내 모터의 encoder CPR를 설정합니다. `ENCODER_CPR=1320`은 출력축 1회전의 x4 count 예시입니다. 모터축의 PPR와 기어 감속 후 바퀴축 CPR, A 상승 edge만 센 count는 같은 값이 아닙니다. 바퀴를 한 바퀴 돌려 encoder tick 차이로 확인합니다. PI gains/FF/PWM limit도 예시이며 부하와 driver에 맞게 조정합니다.

UNO sketch는 pin-change interrupt로 네 쌍의 A/B를 읽으므로 UNO R4나 다른 MCU에 그대로 업로드하지 않습니다. Firmware는 로컬 컴퓨터에서 업로드한 뒤 USB를 Jetson으로 옮겨도 됩니다.

[Arduino CLI 설치](https://docs.arduino.cc/arduino-cli/installation/) 후, 02 폴더에서:

```bash
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli compile --fqbn arduino:avr:uno firmware/encoder_motor
arduino-cli board list
```

Bridge와 Serial Monitor가 포트를 사용하지 않는 상태에서 **board list로 확인한 내 UNO의 포트**를 지정합니다. 아래 `/dev/ttyACM0`은 예시입니다:

```bash
arduino-cli upload --fqbn arduino:avr:uno --port /dev/ttyACM0 firmware/encoder_motor
```

Arduino IDE에서는 같은 .ino를 열고 Arduino UNO와 포트를 선택해 업로드할 수 있습니다. 기존 firmware를 교체하는 작업이므로 대상 보드를 확인합니다. 이 자료 작성 중에는 실제 보드 업로드를 하지 않았습니다.

## 5. Jetson에서 실제 serial 연결

```bash
ls /dev/serial/by-id/
ls -l /dev/ttyACM0
id -nG
```

가능하면 by-id 경로를 사용합니다. 접근 권한이 없고 장치 그룹이 dialout이면 `sudo usermod -aG dialout "$USER"` 후 로그아웃/재로그인합니다. 포트를 전체 사용자에게 chmod 777로 여는 방식은 사용하지 않습니다. ROS node와 Serial Monitor가 한 포트를 동시에 열지 않습니다.

먼저 B의 명령 publisher를 종료하고 아래 node를 실행합니다:

```bash
/usr/bin/python3 bridge_node.py --ros-args \
  -p dry_run:=false -p serial_port:=/dev/ttyACM0 \
  -p wheel_radius_m:=0.05 -p half_length_m:=0.15 -p half_width_m:=0.125
```

r은 바퀴 반경[m], half_length/half_width는 로봇 중심에서 바퀴 접촉 중심까지의 앞뒤/좌우 거리[m]입니다. 숫자는 설명용입니다. 실제 측정값을 사용하세요. Bridge는 포트 open 후 UNO reset을 위한 2초를 기다리고 `stop`, `geom`, `sign`, `stream 1`을 차례로 보냅니다. Firmware에도 같은 geometry가 들어갑니다.

Motor 전원을 끈 상태에서 바퀴를 손으로 돌려 `ros2 topic echo /motor/state`의 tick 변화와 방향을 확인합니다. 논리적으로 앞쪽으로 도는 바퀴의 tick이 증가해야 합니다. 방향이 다르면 `encoder_signs`, 모터 명령 방향이 다르면 `motor_signs`를 FL/FR/RL/RR 순서로 +/-1 설정합니다. 예: `-p encoder_signs:='[1,-1,1,-1]'`은 해당 방향으로 검증된 경우에만 사용합니다.

측정 부호가 뒤집혀 있으면 속도 오차를 줄이는 대신 PWM을 키울 수 있으므로 encoder 부호부터 맞춥니다. 배선과 polarity가 확인되면 바퀴를 띄우고 2의 작은 명령을 다시 발행합니다.

## 6. Arduino 안에서 일어나는 일

Serial `m vx vy wz`를 받으면 X-layout 메카넘 목표 rad/s를 계산합니다:

```text
k = half_length + half_width
FL = (vx - vy - k*wz) / r
FR = (vx + vy + k*wz) / r
RL = (vx + vy - k*wz) / r
RR = (vx - vy + k*wz) / r
```

20 ms마다 tick 변화량 / dt로 바퀴 속도를 구하고 목표와 비교합니다. PI + feedforward 출력은 부호 있는 PWM입니다. MDD10A에 PWM 크기와 DIR 방향을 따로 전달합니다. Encoder는 속도를 측정하고 driver는 전류를 공급합니다. Encoder가 driver 역할을 대신하지 않습니다.

```text
measured_rad_s = delta_ticks * 2*pi / CPR / dt
e = target_rad_s - measured_rad_s
PWM = FF*target + Kp*e + Ki*integral(e)
```

출력은 제한되고 포화 방향으로 더 쌓이는 integral은 멈춥니다. 목표가 0이면 PWM과 integral을 0으로 초기화합니다. 바퀴별 PI는 Arduino에 있고, ROS는 로봇 목표 속도를 전달합니다. PWM 한 값이 모든 부하에서 같은 속도를 뜻하지 않습니다.

## 7. 피드백과 정지

Arduino는 10 Hz로 아래 한 줄을 보냅니다:

```text
STATE,<millis>,<fl_ticks>,<fr_ticks>,<rl_ticks>,<rr_ticks>,<fl_pwm>,<fr_pwm>,<rl_pwm>,<rr_pwm>,<mode>
```

Bridge가 이를 `/motor/state`의 String으로 전달합니다. mode=0은 정지, 1은 velocity 제어입니다. Tick과 PWM이 변하는지, 정방향 목표에 encoder 부호가 맞는지 확인합니다. 이 토픽이 곧 map localization이나 TF는 아닙니다.

Publisher를 Ctrl+C로 종료하고 필요하면 한 번 더 0을 보냅니다:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}'
```

Jetson은 새 cmd_vel이 0.5초간 없으면 stop을 보내고, Arduino도 마지막 유효 m 명령이 0.5초간 없으면 PWM=0으로 만듭니다. USB가 끊겨도 Arduino 쪽 watchdog이 남습니다. 재연결 시 자동으로 예전 속도를 재개하지 않고 배선/포트를 확인한 뒤 node를 다시 실행합니다. 소프트웨어 stop은 전원을 끊는 비상 정지와 같지는 않습니다.

## 검증

```bash
python3 test_protocol.py
source /opt/ros/humble/setup.bash
ROS_DOMAIN_ID=169 /usr/bin/python3 test_bridge_ros2.py
```

단위/방향/속도 제한/명령 만료/STATE 형식, 실제 ROS→가상 serial port 송신과 피드백 수신을 확인합니다. Firmware는 UNO 대상으로 compile 확인합니다. 실제 모터 배선·업로드·encoder 파형·부하 tuning은 별도 실물 확인이 필요합니다.

## 참고

- [ROS Twist](https://docs.ros.org/en/humble/p/geometry_msgs/msg/Twist.html)
- [Arduino UNO R3](https://docs.arduino.cc/hardware/uno-rev3/)
- [Arduino CLI](https://docs.arduino.cc/arduino-cli/getting-started/)
- [pySerial](https://pyserial.readthedocs.io/en/latest/pyserial_api.html)
- [코드 출처·라이선스 기록](../../UPSTREAM.md)
