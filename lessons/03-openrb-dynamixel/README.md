# 03 · Jetson + OpenRB로 DYNAMIXEL 기본 사용하기

작성자: 조연우 · yencho929@snu.ac.kr

ROS 없이 USB console부터 시작합니다. Jetson은 명령을 만들고, OpenRB-150은 USB 텍스트를 DYNAMIXEL Protocol 2.0 packet으로 바꿉니다. DYNAMIXEL 내부 제어기가 목표 위치와 encoder 측정을 비교해 모터를 돌립니다. Arduino encoder motor처럼 외부 PWM/DIR driver를 따로 연결하지 않습니다.

## 1. 수업 전 Jetson 준비

[Jetson 공통 셋업](../../setup/JETSON_SETUP.md)을 먼저 완료하세요. 기준: Jetson Orin Nano 8GB / JetPack 6 / Ubuntu 22.04 / 시스템 Python 3.10 / apt `python3-serial`. 이번 회차는 ROS 모듈을 쓰지 않지만 다음 회차를 위해 ROS 2 Humble도 미리 설치합니다.

```bash
git clone https://github.com/merosnurobotics/meroedu-control.git
cd meroedu-control
bash setup/check_jetson.sh
cd lessons/03-openrb-dynamixel
```

## 2. 준비물과 전원

OpenRB-150, XC330 계열의 TTL 3-pin DYNAMIXEL 한 개, 데이터 통신 가능한 USB 케이블, DYNAMIXEL cable, 모터 모델에 맞는 전원이 필요합니다. 이번 예제는 XC330의 **current-based position mode (5)**를 사용합니다. 다른 모델이 같은 모드를 지원한다고 가정하지 마세요.

| 연결 | 역할 |
| --- | --- |
| Jetson USB ↔ OpenRB USB | 명령·응답, host baud 115200 |
| OpenRB DXL port ↔ XC330 TTL 3-pin | GND / VDD / DATA, half-duplex bus |
| 규격 전원 → OpenRB external terminal | DYNAMIXEL 전력 공급, jumper를 VIN(DXL)로 설정 |

전원이 꺼진 상태에서 배선합니다. OpenRB는 전원 전압을 DYNAMIXEL bus로 넘깁니다. 임의로 5V/12V를 공통 적용하지 마세요. 예를 들어 **XC330-T288은 6.5~12.0V, 권장 11.1V**, XC330-M288은 별도 저전압 사양이므로 모터 라벨과 해당 모델 eManual을 확인하세요. Jetson USB에서 모터 전력을 끌어 쓰지 않습니다. RS-485 모델을 TTL port에 직접 연결하지 않습니다.

첫 실습은 링크·집게·하중을 떼고 모터 하나를 고정하여 진행합니다. `STOP`은 torque OFF라 축을 붙잡지 않습니다. 하중이 매달린 리프트의 정지 방법으로 이 예제를 사용하면 안 됩니다.

## 3. ID / baud를 먼저 확인

[DYNAMIXEL Wizard 2.0](https://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_wizard2/)에서 모터 하나만 연결해 ID와 baud를 읽고 필요하면 설정합니다. 준비 기준은 **ID 0, DXL baud 1,000,000, Protocol 2.0**입니다. 이것은 factory default라는 뜻이 아닙니다. 보통 처음 구매한 모터 설정과 다를 수 있습니다. 다른 ID를 유지하려면 sketch의 `DXL_ID`를 수정합니다.

OpenRB를 Wizard adapter로 쓸 때는 `usb_to_dynamixel` passthrough sketch가 필요합니다. Board package의 예제를 업로드하고 Wizard에서 scan하세요. 아래 교육용 ASCII firmware는 Wizard passthrough가 아닙니다. Wizard를 닫은 다음 교육용 firmware를 업로드합니다. 같은 USB를 두 프로그램이 동시에 열지 않습니다.

## 4. Firmware 준비와 업로드

Arduino IDE의 Additional Boards Manager URLs에 다음 URL을 추가합니다.

```
https://raw.githubusercontent.com/ROBOTIS-GIT/OpenRB-150/master/package_openrb_index.json
```

Boards Manager에서 Arduino SAMD Boards와 OpenRB-150을 설치하고, Library Manager에서 Dynamixel2Arduino를 설치합니다. Tools에서 OpenRB-150 board와 실제 USB port를 선택해 `firmware/openrb_dynamixel/openrb_dynamixel.ino`를 열고 Verify 후 Upload합니다. 펌웨어는 `Serial1`, direction pin `-1`, bus 1 Mbps를 사용합니다.

CLI를 이미 설치했다면 강의 폴더에서:

```bash
BOARD_URL=https://raw.githubusercontent.com/ROBOTIS-GIT/OpenRB-150/master/package_openrb_index.json
arduino-cli core update-index --additional-urls "$BOARD_URL"
arduino-cli core install arduino:samd
arduino-cli core install OpenRB-150:samd@0.2.1 --additional-urls "$BOARD_URL"
arduino-cli lib install Dynamixel2Arduino@0.8.2
arduino-cli compile --fqbn OpenRB-150:samd:OpenRB-150 firmware/openrb_dynamixel
# 아래 PORT는 실제 장치 경로로 바꿉니다. 업로드는 재부팅을 일으킵니다.
PORT=/dev/serial/by-id/여기에는-실제-장치명
arduino-cli upload -p "$PORT" --fqbn OpenRB-150:samd:OpenRB-150 firmware/openrb_dynamixel
```

컴파일 검증 버전은 최종 README의 검증 항목을 확인하세요. Upload가 실패하면 USB data cable·port·board를 확인하고 [OpenRB eManual](https://emanual.robotis.com/docs/en/parts/controller/openrb-150/)의 bootloader 진입 절차를 따릅니다. 모터 전원은 꺼두고 업로드하세요.

## 5. Console로 단계별 사용

```bash
PORT=/dev/serial/by-id/여기에는-실제-장치명
/usr/bin/python3 serial_console.py --port "$PORT"
```

console에 **한 줄씩 입력하고 응답을 확인**합니다.

```
DXL_POWER_ON
PING
INIT
STATUS?
TORQUE_ON
MOVE_DELTA 32
STATUS?
STOP
DXL_POWER_OFF
```

| 명령 | 의미 / 기대 응답 |
| --- | --- |
| DXL_POWER_ON | OpenRB power FET ON. 아직 torque는 OFF. OK_POWER_ON_TORQUE_OFF |
| PING | 설정된 ID만 응답하는지 확인. OK_PING MODEL=… |
| INIT | Torque OFF, mode 5, Goal Current raw 80, profile 20/5, 현재 위치를 목표로 기록. OK_INIT_TORQUE_OFF |
| TORQUE_ON | 현재 위치를 다시 goal에 넣은 뒤 torque ON. OK_TORQUE_ON |
| MOVE_DELTA 32 | 현재 측정 위치에서 +32 ticks, 약 2.8°. OK_MOVE는 쓰기 성공이지 도착 완료가 아님 |
| STATUS? | 위치·전류·전압·hardware error·실제 torque register 읽기 |
| STOP | Torque OFF. 브레이크나 비상정지 장치가 아님 |
| DXL_POWER_OFF | Torque OFF 요청 후 bus 전원 OFF |

4096 ticks = 360°이므로 32 ticks = 2.8125°입니다. 예제는 명령당 ±64 ticks까지만 허용하고 0~4095 밖의 목표를 거절합니다. 기계적 충돌을 판별하는 기능은 없으므로 장착된 관절에 무조건 적용하지 않습니다. `MOVE_DELTA`는 한 번만 보내세요. 반복하면 상대 이동이 계속 누적됩니다.

**Torque ON이 위치 기준을 바꿀 수 있어** enable 직전에 현재 single-turn 위치를 읽어 goal로 설정합니다. 이 예제는 multi-turn 위치 추적과 homing을 다루지 않습니다. `INIT`은 mode register를 쓰므로 필요할 때만 실행하고 반복 publish하지 않습니다.

## 6. Feedback과 실패 확인

예시 응답(형식 설명용, 실제 측정값 아님):

```
STATE POWER=1 READY=1 TORQUE=1 POSITION=2080 CURRENT_RAW=15 VOLTAGE_RAW=111 HW_ERROR=0 TORQUE_READ=1 VALID=1
```

`POSITION`은 실제 encoder 위치입니다. `CURRENT_RAW`, `VOLTAGE_RAW`는 모델별 control table 단위를 적용해야 합니다. XC330-T288에서 전류는 1 mA/LSB, 전압은 0.1 V/LSB입니다. `TORQUE`는 프로그램이 마지막으로 요청한 상태, `TORQUE_READ`는 실제 register입니다. 둘이 다르면 읽기 오류·shutdown을 확인합니다. VALID=0이면 통신 오류나 motor alert가 있어 숫자를 유효한 측정값으로 쓰지 않습니다.

- ERR_NO_RESPONSE: 전원 LED, ID, DXL baud, TTL cable, Protocol 확인. USB baud 115200과 DXL baud 1 Mbps는 별개입니다.
- ERR_INIT: mode 지원 여부와 모델 확인. 현재 제한에 맞지 않는 값은 쓰기 실패할 수 있습니다.
- ERR_POSITION_LIMIT: 현재 위치와 목표가 single-turn 범위 안인지 확인합니다.
- STOP_BUS_OR_HARDWARE_ERROR: 통신 또는 hardware error로 torque OFF를 요청한 상태입니다. 원인을 해결한 뒤 명시적으로 다시 초기화합니다.

console는 0.5초마다 STATUS?를 보내 통신을 유지합니다. 유효한 통신이 3초 이상 끊기면 firmware가 torque OFF를 요청합니다. 케이블 단절이나 모터 자체 오류에서는 이 요청도 전달되지 않을 수 있으므로 전원을 직접 끊을 수 있어야 합니다. console 종료 시 STOP을 보냅니다. 재연결 후 자동으로 이전 이동을 재실행하지 않습니다.

## 다음 회차

[04 · ROS 2 토픽으로 DYNAMIXEL 제어하기](../04-ros2-dynamixel/README.md)에서 **같은 firmware**에 ROS bridge만 추가합니다.

참고: [OpenRB-150](https://emanual.robotis.com/docs/en/parts/controller/openrb-150/), [XC330-T288 control table](https://emanual.robotis.com/docs/en/dxl/x/xc330-t288/), [출처와 라이선스](../../UPSTREAM.md).

## 컴파일 검증

Arduino CLI 1.5.1 / OpenRB-150:samd 0.2.1 / Dynamixel2Arduino 0.8.2로 compile를 통과했습니다(2026-10-08). 실제 hardware upload·모터 동작 검증은 수행하지 않았습니다. Protocol의 이동 범위와 개행 거절은 `python3 test_protocol.py`로 확인합니다.
