# 01 · PID control

P·I·D의 계산과 PID를 적용할 목표·측정·오차·출력의 관계를 살펴봅니다. 시뮬레이션 결과를 바탕으로 한 강의나 실행 demo는 포함하지 않습니다.

Python 3.10 이상. 표준 라이브러리만 사용합니다. 실제 hardware를 구동하지 않습니다.

## 핵심 코드

`pid.py`의 `encoder_speed`: 보정한 wheel CPR, tick 변화량, dt로 실제 회전 속도를 계산합니다.

`PID.step`: 목표와 측정값의 오차를 P·I·D로 계산하고, 출력·적분 제한과 conditional anti-windup을 적용합니다.

`line_command`: 지도에 정한 수평 line의 횡오차를 이동 보정으로 연결하는 작은 예시입니다. 메카넘의 옆방향 이동을 가정하며, 차동 구동 로봇에는 직접 적용하지 않습니다.

## PID 활용 예시

| 대상 | 목표 | 측정 | 오차 | 바꾸는 출력 |
| --- | --- | --- | --- | --- |
| Encoder motor | 바퀴 회전 속도 | Encoder로 얻은 속도 | 목표 − 측정 | Driver PWM |
| 정해진 line 따라가기 | 경로 유지 | Localization 또는 선의 위치 | 경로 이탈 | 이동·회전 명령 |

원본 ddonggae motor 제어는 PI + feedforward, 경로 제어는 P 중심 보정 + deadband + 제한 + 진행 감속입니다. 반드시 세 항 모두를 써야 한다는 사례가 아닙니다. 지속 오차에 I, 빠른 변화나 진동에 D가 필요한지를 측정 특성과 함께 판단합니다.

## 계산 검증

```bash
python3 -m unittest discover -s tests
```

단위·부호, 출력 포화, 좌표 회전, line 보정 방향과 dt 오류를 확인합니다. 실제 모터·로봇에서의 성능 검증은 아닙니다. [원본 출처](../../UPSTREAM.md)
