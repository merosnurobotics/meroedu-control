/* Velocity-only UNO R3 / ATmega328P example. Third-party record: ../../../../UPSTREAM.md.
   X-layout mecanum, FL FR RL RR. MDD10A sign-magnitude PWM/DIR, 115200 baud.
   Edit measured CPR, PI gains and polarity before real motor tests. */
#include <Arduino.h>
#include <avr/interrupt.h>
#include <util/atomic.h>
#include <stdlib.h>
#include <math.h>

const uint8_t DIR_PINS[4] = {4, 7, 2, 12};
const uint8_t PWM_PINS[4] = {5, 6, 3, 10};
const uint8_t ENC_A[4] = {8, A0, A2, 11};
const uint8_t ENC_B[4] = {9, A1, A3, A5};
// Counts per OUTPUT wheel revolution with all A/B edges (x4), not motor-shaft PPR.
const float ENCODER_CPR = 1320.0f; // Example only: measure your geared encoder.
const float KP = 10.0f, KI = 8.0f, FF = 14.0f;
const int MAX_PWM = 180;
const float MAX_WHEEL_RAD_S = 6.0f;
float radiusM = 0.05f, halfLengthM = 0.15f, halfWidthM = 0.125f;
int8_t motorSign[4] = {1, 1, 1, 1}, encoderSign[4] = {1, 1, 1, 1};
volatile long ticks[4] = {0, 0, 0, 0};
volatile uint8_t prevState[4];
long lastTicks[4] = {0, 0, 0, 0};
float target[4] = {0, 0, 0, 0}, integral[4] = {0, 0, 0, 0};
int pwmOutput[4] = {0, 0, 0, 0};
bool enabled = false, streaming = true;
unsigned long lastCommand = 0, lastControl = 0, lastReport = 0;
char lineBuffer[64]; uint8_t lineLength = 0; bool discardLine = false;

void readEncoderStates(uint8_t *states) {
  const uint8_t b = PINB, c = PINC;
  states[0] = ((b & _BV(PB0)) ? 2 : 0) | ((b & _BV(PB1)) ? 1 : 0);
  states[1] = ((c & _BV(PC0)) ? 2 : 0) | ((c & _BV(PC1)) ? 1 : 0);
  states[2] = ((c & _BV(PC2)) ? 2 : 0) | ((c & _BV(PC3)) ? 1 : 0);
  states[3] = ((b & _BV(PB3)) ? 2 : 0) | ((c & _BV(PC5)) ? 1 : 0);
}
void encoderChanged() {
  const int8_t delta[16] = {0,-1,1,0,1,0,0,-1,-1,0,0,1,0,1,-1,0};
  uint8_t states[4]; readEncoderStates(states);
  for (uint8_t i = 0; i < 4; ++i) {
    ticks[i] += delta[(prevState[i] << 2) | states[i]] * encoderSign[i];
    prevState[i] = states[i];
  }
}
ISR(PCINT0_vect) { encoderChanged(); }
ISR(PCINT1_vect) { encoderChanged(); }
void writePwm(uint8_t wheel, int value) {
  value = constrain(value, -MAX_PWM, MAX_PWM);
  pwmOutput[wheel] = value;
  const int physical = value * motorSign[wheel];
  digitalWrite(DIR_PINS[wheel], physical >= 0 ? LOW : HIGH);
  analogWrite(PWM_PINS[wheel], abs(physical));
}
void stopMotors() {
  enabled = false;
  for (uint8_t i = 0; i < 4; ++i) {
    target[i] = 0; integral[i] = 0; writePwm(i, 0);
  }
}
bool parseFloat(char *token, float &value) {
  if (!token) return false;
  char *end; value = strtod(token, &end);
  return end != token && *end == '\0' && isfinite(value);
}
void command(char *line) {
  char *name = strtok(line, " \r");
  if (!name) return;
  if (!strcmp(name, "stop")) { stopMotors(); return; }
  float args[8]; uint8_t n = 0;
  char *token;
  while ((token = strtok(NULL, " \r"))) {
    if (n == 8 || !parseFloat(token, args[n])) { stopMotors(); return; }
    ++n;
  }
  if (!strcmp(name, "m") && n == 3) {
    const float vx = args[0], vy = args[1], k = halfLengthM + halfWidthM, wz = args[2];
    float wheel[4] = {(vx-vy-k*wz)/radiusM, (vx+vy+k*wz)/radiusM,
                      (vx+vy-k*wz)/radiusM, (vx-vy+k*wz)/radiusM};
    float scale = 1.0f;
    for (uint8_t i = 0; i < 4; ++i) {
      if (!isfinite(wheel[i])) { stopMotors(); return; }
      scale = max(scale, abs(wheel[i]) / MAX_WHEEL_RAD_S);
    }
    for (uint8_t i = 0; i < 4; ++i) target[i] = wheel[i] / scale;
    enabled = true; lastCommand = millis();
  } else if (!strcmp(name, "geom") && n == 3 && args[0] > 0 && args[1] > 0 && args[2] > 0) {
    stopMotors(); radiusM = args[0]; halfLengthM = args[1]; halfWidthM = args[2];
  } else if (!strcmp(name, "sign") && n == 8) {
    for (uint8_t i = 0; i < 8; ++i) if (args[i] != 1 && args[i] != -1) { stopMotors(); return; }
    stopMotors();
    ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
      for (uint8_t i = 0; i < 4; ++i) { motorSign[i] = (int8_t)args[i]; encoderSign[i] = (int8_t)args[i+4]; }
    }
  } else if (!strcmp(name, "stream") && n == 1 && (args[0] == 0 || args[0] == 1)) {
    streaming = args[0] == 1;
  } else { stopMotors(); Serial.println(F("ERR command")); }
}
void readSerial() {
  uint8_t budget = 64;
  while (Serial.available() && budget--) {
    char c = Serial.read();
    if (c == '\n') {
      if (!discardLine) { lineBuffer[lineLength] = 0; command(lineBuffer); }
      lineLength = 0; discardLine = false;
    } else if (!discardLine) {
      if (lineLength < sizeof(lineBuffer)-1) lineBuffer[lineLength++] = c;
      else { discardLine = true; lineLength = 0; stopMotors(); }
    }
  }
}
void control(unsigned long now) {
  if (enabled && now-lastCommand > 500) stopMotors();
  if (now-lastControl < 20) return;
  const float dt = (now-lastControl) * 0.001f; lastControl = now;
  long current[4];
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { for (uint8_t i = 0; i < 4; ++i) current[i] = ticks[i]; }
  for (uint8_t i = 0; i < 4; ++i) {
    const float measured = (current[i]-lastTicks[i]) * TWO_PI / ENCODER_CPR / dt;
    lastTicks[i] = current[i];
    if (!enabled || abs(target[i]) < 0.01f) { integral[i] = 0; writePwm(i, 0); continue; }
    const float error = target[i]-measured;
    const float candidate = constrain(integral[i]+error*dt, -8.0f, 8.0f);
    const float raw = FF*target[i] + KP*error + KI*candidate;
    // Conditional anti-windup: integrate only when not pushing further into saturation.
    if ((raw <= MAX_PWM && raw >= -MAX_PWM) || (raw > MAX_PWM && error < 0) || (raw < -MAX_PWM && error > 0)) integral[i] = candidate;
    const float output = FF*target[i] + KP*error + KI*integral[i];
    writePwm(i, (int)round(constrain(output, -MAX_PWM, MAX_PWM)));
  }
}
void report(unsigned long now) {
  if (!streaming || now-lastReport < 100) return;
  lastReport = now; long current[4];
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { for (uint8_t i = 0; i < 4; ++i) current[i] = ticks[i]; }
  Serial.print(F("STATE,")); Serial.print(now);
  for (uint8_t i = 0; i < 4; ++i) { Serial.print(','); Serial.print(current[i]); }
  for (uint8_t i = 0; i < 4; ++i) { Serial.print(','); Serial.print(pwmOutput[i]); }
  Serial.print(','); Serial.println(enabled ? 1 : 0);
}
void setup() {
  Serial.begin(115200);
  for (uint8_t i = 0; i < 4; ++i) {
    pinMode(DIR_PINS[i], OUTPUT); pinMode(PWM_PINS[i], OUTPUT);
    pinMode(ENC_A[i], INPUT_PULLUP); pinMode(ENC_B[i], INPUT_PULLUP);
  }
  stopMotors(); uint8_t states[4]; readEncoderStates(states);
  for (uint8_t i = 0; i < 4; ++i) prevState[i] = states[i];
  PCMSK0 = _BV(PCINT0) | _BV(PCINT1) | _BV(PCINT3);
  PCMSK1 = _BV(PCINT8) | _BV(PCINT9) | _BV(PCINT10) | _BV(PCINT11) | _BV(PCINT13);
  PCIFR = _BV(PCIF0) | _BV(PCIF1); PCICR |= _BV(PCIE0) | _BV(PCIE1);
  lastControl = millis(); Serial.println(F("READY encoder_motor"));
}
void loop() { readSerial(); const unsigned long now = millis(); control(now); report(now); }
