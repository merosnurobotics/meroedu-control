# 01 · PID control

목표·측정·오차부터 encoder motor와 지도 line tracking까지 작은 시뮬레이션으로 실행합니다. Python 3.10 이상, 추가 package와 실제 모터 불필요.

```bash
python3 demo.py --output output
python3 -m unittest discover -s tests
```

## 결과

- `motor-p.csv`, `motor-pi.csv`, `motor-pid.csv`: 시간, 목표 rad/s, encoder를 모사한 측정 rad/s, PWM.
- `line.csv`: 시간, 지도 x/y, 이동 속도 vx/vy.
- 모터는 first-order toy model입니다. 1초에 목표 5 rad/s를 주고 6초에 부하를 변경합니다. line은 y=0으로 복귀하고 4초에 측방 교란을 줍니다.
- **실제 모터 측정이나 원본 경기 데이터가 아닙니다.**

## 원본과 교육용 확장

ddonggae encoder firmware의 기본값은 Kp=10, Ki=8, Kd=0인 **PI** + feedforward입니다. `navigation/street_nav.py` 경로 제어는 횡방향 **P** 보정 + deadband + 속도 제한 + 이탈 시 진행 감속입니다. 원본이 전 구간 PID를 쓴다고 설명하지 않습니다.

`pid.py`는 이 구성을 교육용으로 재작성하고 선택 가능한 I/D와 conditional anti-windup을 더했습니다. `encoder_speed`에는 바퀴 한 바퀴에서 보정한 count(CPR)를 사용하세요. 예제 1320 CPR은 다른 모터의 보장값이 아닙니다.

Line은 지도에 정한 수평 경로이고 검은 테이프를 감지하는 광센서 실습이 아닙니다. 메카넘의 sideways motion을 가정합니다. 차동 구동 로봇은 vy를 직접 실행할 수 없으므로 steering/yaw 방식으로 바꿔야 합니다.

## 따라할 실험

1. 모터 P만 실행한 뒤 PI를 비교합니다. 부하 변화 뒤 잔여 오차를 확인합니다.
2. D를 작은 값으로 넣고 encoder quantization이 출력을 흔드는지 봅니다.
3. Line의 Ki를 작게 켜고 일정 교란의 잔여 오차와 overshoot를 비교합니다.
4. output limit을 줄여 포화 중 적분이 계속 커지는지 확인합니다.

CSV는 spreadsheet에서도 그릴 수 있습니다. 사이트 그림은 이 코드의 출력으로 생성했습니다. 실제 PWM pin이나 serial command를 보내지 않습니다. 실물에서는 부호·driver 규약·전류 제한을 확인하고 즉시 정지 가능한 작은 출력부터 시작합니다.

## 검증

두 시뮬레이션을 실행했고 encoder 단위/부호, 출력 포화의 anti-windup, body frame 회전, line 복귀, dt 오류를 검증했습니다. [UPSTREAM](../../UPSTREAM.md).
