"""Small, allowlisted USB text protocol; not a DYNAMIXEL packet encoder."""
import re

COMMANDS = {'DXL_POWER_ON', 'DXL_POWER_OFF', 'PING', 'INIT', 'TORQUE_ON', 'STOP', 'STATUS?'}

def command_line(text):
    if '\n' in text or '\r' in text:
        raise ValueError('One command per message')
    value = text.strip()
    if value in COMMANDS:
        return value + '\n'
    match = re.fullmatch(r'MOVE_DELTA (-?\d{1,2})', value)
    if match and 0 < abs(int(match[1])) <= 64:
        return f'MOVE_DELTA {int(match[1])}\n'
    raise ValueError('Unsupported command or delta outside +/-64 ticks')
