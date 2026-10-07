# 04 · ROS 2 토픽으로 DYNAMIXEL 제어하기

작성자: 조연우 · yencho929@snu.ac.kr

[03 기본 사용](../03-openrb-dynamixel/README.md)에서 배선·ID·baud·firmware와 console 동작을 먼저 확인하세요. 이번 회차는 그 USB interface 앞에 ROS 2 node를 연결합니다. 다른 로봇 저장소, camera, 데이터, 모델 가중치는 필요 없습니다.

## 환경

[Jetson 공통 셋업](../../setup/JETSON_SETUP.md): Ubuntu 22.04 / ROS 2 Humble / 시스템 Python 3.10 / apt python3-serial. `bridge_node.py`는 같은 교육 저장소의 03 `protocol.py`를 가져옵니다. 저장소 전체를 clone하세요.

```bash
git clone https://github.com/merosnurobotics/meroedu-control.git
cd meroedu-control/lessons/04-ros2-dynamixel
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42
```

모든 터미널에서 source와 domain 설정을 반복합니다. 실제 하드웨어에서는 USB console, Wizard, Serial monitor를 종료하고 bridge만 port를 열게 합니다.

## 1. 모터 없이 ROS 메시지 흐름 확인

터미널 A, 강의 폴더에서:

```bash
/usr/bin/python3 bridge_node.py
```

기본 `dry_run=true`라 USB를 열지 않습니다. 터미널 B:

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42
ros2 topic echo /dynamixel/serial_tx std_msgs/msg/String
```

터미널 C:

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42
ros2 topic pub --once /dynamixel/command std_msgs/msg/String "{data: 'MOVE_DELTA 32'}"
```

TX에 MOVE_DELTA 32가 보여야 합니다. STATUS?는 0.5초마다 발행됩니다. dry run에는 모터가 없으므로 측정 feedback이 만들어지지 않습니다. 입력 `String`은 ROS wire message이고 USB 출력은 ASCII 한 줄, 실제 DYNAMIXEL bus에는 OpenRB가 만든 Protocol 2.0 packet이 나갑니다.

## 2. 실제 장치 연결

03을 완료하고 하중 없이 모터 하나를 고정한 뒤 terminal A를 종료하고:

```bash
PORT=/dev/serial/by-id/여기에는-실제-장치명
/usr/bin/python3 bridge_node.py --ros-args -p dry_run:=false -p serial_port:="$PORT"
```

bridge는 연결 시 STOP만 보내며 power/INIT/torque/move를 자동 실행하지 않습니다. 터미널 B에서:

```bash
ros2 topic echo /dynamixel/state std_msgs/msg/String
```

터미널 C에서 각각 응답을 확인한 뒤 다음 명령을 보냅니다:

```bash
ros2 topic pub --once /dynamixel/command std_msgs/msg/String "{data: 'DXL_POWER_ON'}"
ros2 topic pub --once /dynamixel/command std_msgs/msg/String "{data: 'PING'}"
ros2 topic pub --once /dynamixel/command std_msgs/msg/String "{data: 'INIT'}"
ros2 topic pub --once /dynamixel/command std_msgs/msg/String "{data: 'TORQUE_ON'}"
ros2 topic pub --once /dynamixel/command std_msgs/msg/String "{data: 'MOVE_DELTA 32'}"
ros2 topic pub --once /dynamixel/command std_msgs/msg/String "{data: 'STOP'}"
ros2 topic pub --once /dynamixel/command std_msgs/msg/String "{data: 'DXL_POWER_OFF'}"
```

모두 연속으로 붙여 실행하지 말고 한 명령씩 OK/ERR와 실제 상태를 확인합니다. `--once`를 유지하세요. `MOVE_DELTA`는 상대 이동이라 10Hz 반복 publish하면 계속 움직입니다. `INIT`도 mode 변경을 반복하므로 주기적 publish하지 않습니다.

## 3. Topic 계약

| Topic | 타입 | 방향 | 의미 |
| --- | --- | --- | --- |
| /dynamixel/command | std_msgs/msg/String | 입력 | Allowlist의 명령 하나. MOVE_DELTA는 ±64 ticks |
| /dynamixel/serial_tx | std_msgs/msg/String | 출력 | USB로 보내려는 명령. 도착·동작 성공을 보장하지 않음 |
| /dynamixel/state | std_msgs/msg/String | 출력 | OpenRB에서 실제로 읽은 STATE / OK / ERR / STOP 응답 |

개행·지원하지 않는 문자열·범위를 벗어난 이동은 bridge가 거절합니다. node는 0.5초마다 STATUS?를 보내고 firmware는 3초 통신 watchdog을 적용합니다. node 종료 시 STOP, 통신 실패 시 자동 reconnect하지 않습니다. 중력 하중을 지탱하는 기구에 torque OFF watchdog을 그대로 적용하지 마세요.

## 4. 다음 단계 discussion

이 회차의 String 계약은 protocol을 눈으로 확인하기 위한 것입니다. 여러 관절을 제어할 때는 motor ID·목표 위치·단위·timestamp·명령 확인을 담은 typed message나 service/action 계약을 정하고, 실제 도착 판정을 feedback으로 해야 합니다. 여러 subscriber나 sender가 같은 상대 이동을 중복 실행하지 않도록 명령 소유권과 acknowledgment도 설계합니다.

코드 검증은 `test_bridge_ros2.py`로 실제 ROS 2와 pseudo-terminal을 연결해 USB 문자열·응답 흐름을 검사합니다. 이 테스트는 실제 모터 동작이나 전원·기구 안전을 검증하지 않습니다.

```bash
source /opt/ros/humble/setup.bash
ROS_DOMAIN_ID=170 /usr/bin/python3 test_bridge_ros2.py
```
