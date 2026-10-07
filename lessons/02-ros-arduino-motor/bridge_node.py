"""ROS Twist -> `m vx vy wz` serial -> encoder firmware. Dry run by default."""
import math
import time
import termios
import serial
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from protocol import CommandGate, limit_twist, parse_state


class MotorBridge(Node):
    def __init__(self, **kwargs):
        super().__init__('meroedu_motor_bridge', **kwargs)
        for name, value in [('dry_run', True), ('serial_port', '/dev/ttyACM0'),
                            ('serial_boot_delay_sec', 2.0), ('cmd_vel_topic', '/cmd_vel'),
                            ('wheel_radius_m', 0.05), ('half_length_m', 0.15), ('half_width_m', 0.125),
                            ('motor_signs', [1, 1, 1, 1]), ('encoder_signs', [1, 1, 1, 1])]:
            self.declare_parameter(name, value)
        self.geometry = tuple(float(self.get_parameter(p).value) for p in
                              ('wheel_radius_m', 'half_length_m', 'half_width_m'))
        limit_twist(0, 0, 0, *self.geometry)  # Validate setup before opening the port.
        self.gate = CommandGate()
        self.port = None
        self.rx = b''
        self.failed = False
        self.last_logged_line = None
        self.tx_pub = self.create_publisher(String, '/motor/serial_tx', 10)
        self.state_pub = self.create_publisher(String, '/motor/state', 10)
        signs = []
        for name in ('motor_signs', 'encoder_signs'):
            values = self.get_parameter(name).value
            if len(values) != 4 or any(v not in (-1, 1) for v in values):
                raise ValueError('Each motor/encoder sign list must have four +/-1 values')
            signs.extend(values)
        if not self.get_parameter('dry_run').value:
            self.port = serial.Serial(self.get_parameter('serial_port').value, 115200,
                                      timeout=0, write_timeout=0.1, exclusive=True)
            time.sleep(max(0.0, float(self.get_parameter('serial_boot_delay_sec').value)))
            for line in ['stop\n', 'geom {:.5f} {:.5f} {:.5f}\n'.format(*self.geometry),
                         'sign '+' '.join(map(str, signs))+'\n', 'stream 1\n']:
                self.port.write(line.encode('ascii'))
                time.sleep(0.06)
        self.cmd_sub = self.create_subscription(Twist, self.get_parameter('cmd_vel_topic').value,
                                                self.receive, 1)
        self.timer = self.create_timer(0.05, self.tick)
        self.get_logger().info('Dry run: no serial port opened' if self.port is None else 'Serial connected')

    def receive(self, msg):
        values = (msg.linear.x, msg.linear.y, msg.angular.z)
        if not all(math.isfinite(v) for v in values):
            self.gate.received_at = None
            self.get_logger().error('Nonfinite Twist: stop')
            return
        vx, vy = (max(-0.15, min(0.15, v)) for v in values[:2])
        wz = max(-0.5, min(0.5, values[2]))
        self.gate.accept(*limit_twist(vx, vy, wz, *self.geometry), time.monotonic())

    def tick(self):
        line = self.gate.line(time.monotonic())
        msg = String(); msg.data = line.rstrip(); self.tx_pub.publish(msg)
        if line != self.last_logged_line:
            self.get_logger().info('TX '+line.rstrip())
            self.last_logged_line = line
        if self.port is None or self.failed:
            return
        try:
            self.port.write(line.encode('ascii'))
            self.rx += self.port.read(min(self.port.in_waiting, 512))
            if len(self.rx) > 4096:
                self.rx = b''
            while b'\n' in self.rx:
                raw, self.rx = self.rx.split(b'\n', 1)
                text = raw.decode('ascii', errors='replace').strip()
                if parse_state(text) is not None:
                    state = String(); state.data = text; self.state_pub.publish(state)
        except (serial.SerialException, OSError, termios.error) as exc:
            self.failed = True
            self.gate.received_at = None
            self.get_logger().error(f'Serial disconnected: {exc}; restart after checking wiring')
            self.port.close()

    def close(self):
        self.timer.cancel()
        if self.port is not None and self.port.is_open:
            try:
                self.port.write(b'stop\n')
            except (serial.SerialException, OSError, termios.error):
                pass
            self.port.close()


def main():
    rclpy.init()
    node = MotorBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
