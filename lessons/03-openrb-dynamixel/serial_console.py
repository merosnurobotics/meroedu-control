"""USB console, without ROS. No automatic power/torque/movement commands."""
import argparse
import select
import sys
import time
import serial
from protocol import command_line

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True)
    args = parser.parse_args()
    with serial.Serial(args.port, 115200, timeout=0, write_timeout=0.2, exclusive=True) as port:
        time.sleep(2)
        port.write(b'STOP\n')
        print('Connected. Enter a command; Ctrl+C exits. STATUS? heartbeat is automatic.')
        buffer = b''
        next_poll = 0.0
        try:
            while True:
                if time.monotonic() >= next_poll:
                    port.write(b'STATUS?\n')
                    next_poll = time.monotonic() + 0.5
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    text = sys.stdin.readline()
                    if not text:
                        break
                    try:
                        port.write(command_line(text.rstrip('\n')).encode('ascii'))
                    except ValueError as exc:
                        print(exc)
                buffer += port.read(min(port.in_waiting, 512))
                if len(buffer) > 4096:
                    buffer = b''
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    print(line.decode('ascii', errors='replace').strip())
        except KeyboardInterrupt:
            pass
        finally:
            if port.is_open:
                try:
                    port.write(b'STOP\n')
                except (serial.SerialException, OSError):
                    pass

if __name__ == '__main__':
    main()
