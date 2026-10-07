// Educational single-servo interface. Provenance and licenses: repository UPSTREAM.md.
#include <Dynamixel2Arduino.h>
#include <stdlib.h>
#include <string.h>
Dynamixel2Arduino dxl(Serial1, -1);
using namespace ControlTableItem;
const uint8_t DXL_ID = 0;  // Set this to the ID configured with Wizard.
const uint32_t DXL_BAUD = 1000000;
bool powered = false, ready = false, enabled = false;
unsigned long lastCommand = 0, lastHealth = 0;
char input[48];
uint8_t length = 0;
bool overflow = false;

void stopMotor() {
  if (powered) dxl.torqueOff(DXL_ID);
  enabled = false;
}
void powerBus(bool on) {
  stopMotor();
  ready = false;
  pinMode(BDPIN_DXL_PWR_EN, OUTPUT);
  digitalWrite(BDPIN_DXL_PWR_EN, on ? HIGH : LOW);
  powered = on;
  delay(300);
}
bool position(int32_t &value) {
  value = dxl.readControlTableItem(PRESENT_POSITION, DXL_ID);
  return dxl.getLastLibErrCode() == 0 && dxl.getLastStatusPacketError() == 0 && value >= 0 && value <= 4095;
}
bool syncGoal() {
  int32_t value;
  return position(value) && dxl.writeControlTableItem(GOAL_POSITION, DXL_ID, value);
}
void status() {
  Serial.print("STATE POWER="); Serial.print(powered);
  Serial.print(" READY="); Serial.print(ready);
  Serial.print(" TORQUE="); Serial.print(enabled);
  if (powered && dxl.ping(DXL_ID)) {
    const uint8_t items[] = {PRESENT_POSITION, PRESENT_CURRENT, PRESENT_INPUT_VOLTAGE, HARDWARE_ERROR_STATUS, TORQUE_ENABLE};
    const char *labels[] = {" POSITION=", " CURRENT_RAW=", " VOLTAGE_RAW=", " HW_ERROR=", " TORQUE_READ="};
    bool valid = true;
    for (uint8_t i=0; i<5; ++i) {
      int32_t value = items[i] == PRESENT_CURRENT ? (int32_t)dxl.getPresentCurrent(DXL_ID, UNIT_RAW) : dxl.readControlTableItem(items[i], DXL_ID);
      uint8_t error = dxl.getLastLibErrCode();
      if (error || dxl.getLastStatusPacketError()) valid = false;
      Serial.print(labels[i]); Serial.print(value);
    }
    Serial.print(" VALID="); Serial.print(valid);
  } else Serial.print(" LINK=NO_RESPONSE VALID=0");
  Serial.println();
}
void command(char *line) {
  lastCommand = millis();
  if (!strcmp(line, "STOP")) { stopMotor(); Serial.println("OK_STOP"); return; }
  if (!strcmp(line, "DXL_POWER_OFF")) { powerBus(false); Serial.println("OK_POWER_OFF"); return; }
  if (!strcmp(line, "DXL_POWER_ON")) { powerBus(true); Serial.println("OK_POWER_ON_TORQUE_OFF"); return; }
  if (!strcmp(line, "STATUS?")) { status(); return; }
  if (!powered) { Serial.println("ERR_POWER_OFF"); return; }
  if (!strcmp(line, "PING")) {
    if (dxl.ping(DXL_ID)) { Serial.print("OK_PING MODEL="); Serial.println(dxl.getModelNumber(DXL_ID)); }
    else Serial.println("ERR_NO_RESPONSE");
    return;
  }
  if (!strcmp(line, "INIT")) {
    stopMotor(); ready = false;
    // XC330 current-based position, with modest raw RAM settings; EEPROM ID/baud unchanged.
    ready = dxl.ping(DXL_ID) && dxl.torqueOff(DXL_ID)
      && dxl.setOperatingMode(DXL_ID, OP_CURRENT_BASED_POSITION)
      && dxl.writeControlTableItem(GOAL_CURRENT, DXL_ID, 80)
      && dxl.writeControlTableItem(PROFILE_VELOCITY, DXL_ID, 20)
      && dxl.writeControlTableItem(PROFILE_ACCELERATION, DXL_ID, 5)
      && syncGoal();
    Serial.println(ready ? "OK_INIT_TORQUE_OFF" : "ERR_INIT"); return;
  }
  if (!strcmp(line, "TORQUE_ON")) {
    enabled = ready && syncGoal() && dxl.torqueOn(DXL_ID);
    Serial.println(enabled ? "OK_TORQUE_ON" : "ERR_TORQUE_ON"); return;
  }
  if (!strncmp(line, "MOVE_DELTA ", 11)) {
    char *end; long delta = strtol(line + 11, &end, 10);
    int32_t now;
    if (!ready || !enabled || end == line + 11 || *end || delta == 0 || delta < -64 || delta > 64 || !position(now)) {
      Serial.println("ERR_MOVE"); return;
    }
    long goal = now + delta;
    if (goal < 0 || goal > 4095) { Serial.println("ERR_POSITION_LIMIT"); return; }
    Serial.println(dxl.writeControlTableItem(GOAL_POSITION, DXL_ID, goal) ? "OK_MOVE" : "ERR_WRITE"); return;
  }
  Serial.println("ERR_COMMAND");
}
void setup() {
  Serial.begin(115200);
  dxl.begin(DXL_BAUD); dxl.setPortProtocolVersion(2.0);
  powerBus(false);
  Serial.println("READY_POWER_OFF");
}
void loop() {
  uint8_t budget = 64;
  while (Serial.available() && budget--) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      if (overflow) { stopMotor(); Serial.println("ERR_LINE_LENGTH"); }
      else { input[length] = 0; command(input); }
      length = 0; overflow = false;
    } else if (!overflow) {
      if (length < sizeof(input)-1) input[length++] = c;
      else overflow = true;
    }
  }
  if (enabled && millis() - lastCommand > 3000) {
    stopMotor(); Serial.println("STOP_WATCHDOG");
  }
  if (enabled && millis() - lastHealth > 250) {
    lastHealth = millis();
    int32_t error = dxl.readControlTableItem(HARDWARE_ERROR_STATUS, DXL_ID);
    if (dxl.getLastLibErrCode() != 0 || dxl.getLastStatusPacketError() != 0 || error != 0) {
      stopMotor(); ready = false; Serial.println("STOP_BUS_OR_HARDWARE_ERROR");
    }
  }
}
