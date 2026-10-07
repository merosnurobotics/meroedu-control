# Copyright 2026 mero14
# Copyright 2026 MERO educational adaptations
# SPDX-License-Identifier: Apache-2.0
# Modified educational interface; see ../../UPSTREAM.md and ../../LICENSES/Apache-2.0.txt.
"""ROS String -> OpenRB USB text commands. Dry run by default, no auto torque."""
from pathlib import Path
import sys
import time
import termios
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03-openrb-dynamixel'))
from protocol import command_line
import serial
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class DynamixelBridge(Node):
    def __init__(self, **kwargs):
        super().__init__('meroedu_dynamixel_bridge', **kwargs)
        self.declare_parameter('dry_run', True)
        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('serial_boot_delay_sec', 2.0)
        self.port = None
        self.failed = False
        self.rx = b''
        self.tx = self.create_publisher(String, '/dynamixel/serial_tx', 10)
        self.state = self.create_publisher(String, '/dynamixel/state', 10)
        if not self.get_parameter('dry_run').value:
            self.port = serial.Serial(self.get_parameter('serial_port').value, 115200,
                                      timeout=0, write_timeout=0.2, exclusive=True)
            time.sleep(max(0, float(self.get_parameter('serial_boot_delay_sec').value)))
            self.port.write(b'STOP\n')
        self.sub = self.create_subscription(String, '/dynamixel/command', self.receive, 1)
        self.timer = self.create_timer(0.05, self.tick)
        self.next_poll = 0.0
        self.get_logger().info('Ready; power and torque require explicit commands')

    def send(self, line):
        if self.failed:
            return
        msg = String(); msg.data = line.rstrip(); self.tx.publish(msg)
        if self.port is None:
            return
        try:
            self.port.write(line.encode('ascii'))
        except (serial.SerialException, OSError, termios.error) as exc:
            self.fail(exc)

    def receive(self, msg):
        try:
            self.send(command_line(msg.data))
        except ValueError as exc:
            self.get_logger().warning(str(exc))

    def fail(self, exc):
        self.failed = True
        self.get_logger().error(f'USB disconnected: {exc}; no automatic reconnect')
        if self.port is not None:
            self.port.close()

    def tick(self):
        if time.monotonic() >= self.next_poll:
            self.send('STATUS?\n')
            self.next_poll = time.monotonic() + 0.5
        if self.port is None or self.failed:
            return
        try:
            self.rx += self.port.read(min(self.port.in_waiting, 512))
            if len(self.rx) > 4096:
                self.rx = b''
            while b'\n' in self.rx:
                raw, self.rx = self.rx.split(b'\n', 1)
                value = raw.decode('ascii', errors='replace').strip()
                if value.startswith(('STATE ', 'OK_', 'ERR_', 'STOP_')):
                    msg = String(); msg.data = value; self.state.publish(msg)
        except (serial.SerialException, OSError, termios.error) as exc:
            self.fail(exc)

    def close(self):
        self.timer.cancel()
        if self.port is not None and self.port.is_open:
            try:
                self.port.write(b'STOP\n')
            except (serial.SerialException, OSError, termios.error):
                pass
            self.port.close()

def main():
    rclpy.init()
    node = DynamixelBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close(); node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()

if __name__ == '__main__':
    main()
