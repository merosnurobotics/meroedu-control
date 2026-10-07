# 원본 출처

Team 14 · MIT · ddonggae 고정 commit `d85758c752e6cd3244e16d9ea4a3d2831da225b4`

- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/hardware/firmware/arduino_mecanum/mecanum_encoder_control.ino
- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/navigation/street_nav.py

교육용으로 핵심 함수와 실행 예제를 재구성했습니다. 원본 데이터와 하드웨어별 설정은 복사하지 않았습니다.

## 02 · ROS/Arduino motor pipeline

기준 commit: d85758c752e6cd3244e16d9ea4a3d2831da225b4 (Team 14, MIT)

- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/hardware/ros2/robot_hardware/robot_hardware/mecanum_bridge_node.py
- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/hardware/ros2/robot_hardware/robot_hardware/mecanum_control.py
- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/hardware/firmware/arduino_mecanum/mecanum_encoder_control.ino
- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/hardware/docs/wiring-and-firmware.md

Velocity-only로 재구성했습니다. m/stop/geom/sign/stream과 STATE 형식, 실제 UNO/MDD10A pin layout, encoder tick 기반 speed feedback을 유지했습니다. Position primitives/odometry/TF/재접속/실기 보드별 workaround는 제외하고, PI conditional anti-windup과 기본 dry-run을 적용했습니다. Geometry/CPR/gains는 실습 예시로 별도 보정합니다. 원본의 실제 firmware CPR(1320)와 일부 bridge 기본값(2464)이 달라 실습에서는 동일 count 규약을 측정해 설정하도록 안내합니다.

## 03 / 04 · OpenRB + DYNAMIXEL

기준 commit: d85758c752e6cd3244e16d9ea4a3d2831da225b4

- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/hardware/firmware/openrb_gripper_mast/openrb_gripper.ino (Team 14, MIT)
- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/hardware/ros2/robot_hardware/robot_hardware/gripper_bridge_node.py (Copyright 2026 mero14, Apache-2.0)
- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/docs/04-getting-started.md
- https://github.com/YenCho/ddonggae/blob/d85758c752e6cd3244e16d9ea4a3d2831da225b4/docs/08-reproducibility.md

Serial1 / direction pin -1 / Protocol 2.0 / 1Mbps / ID 0과 current-based position을 참고했습니다. 기구 고유 각도, 집게/리프트 state machine, multi-turn stroke는 제거했습니다. INIT·torque ON을 power ON에서 분리하고 작은 single-turn 상대 이동, 명시적 명령, torque OFF watchdog으로 재구성했습니다. 실제 Jetson 기준 환경(Orin Nano8GB, JetPack6, Ubuntu22.04, Humble, Python3.10)을 재사용하되 불필요한 camera/GPU 의존성은 제외했습니다. 펌웨어·Python 예제는 교육 저장소만으로 실행합니다.

03 기본 사용과 04 ROS bridge는 같은 ASCII firmware를 공유합니다. Firmware 명령은 원본과 완전 호환되는 interface가 아닙니다. 원본 gripper bridge의 Apache-2.0 notice를 보존한 별도 `LICENSES/Apache-2.0.txt`와 04 파일의 notice를 참고하세요. Dynamixel2Arduino는 ROBOTIS의 Apache-2.0 라이브러리로 Library Manager에서 별도 설치하며 vendoring하지 않습니다.
