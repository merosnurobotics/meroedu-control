"""Real ROS + pseudo-terminal protocol test, NOT a motor or firmware simulation."""
import os
import pty
import time
import unittest
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.executors import SingleThreadedExecutor
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from bridge_node import MotorBridge


class BridgeTest(unittest.TestCase):
    def test_ros_serial_feedback_and_timeout(self):
        master, slave = pty.openpty()
        os.set_blocking(master, False)
        rclpy.init()
        bridge = MotorBridge(parameter_overrides=[Parameter('dry_run', value=False),
            Parameter('serial_port', value=os.ttyname(slave)),
            Parameter('serial_boot_delay_sec', value=0.0)])
        client = Node('meroedu_bridge_test')
        received = []
        client.create_subscription(String, '/motor/state', lambda msg: received.append(msg.data), 10)
        pub = client.create_publisher(Twist, '/cmd_vel', 10)
        cmd = Twist(); cmd.linear.x = 0.05
        timer = client.create_timer(0.1, lambda: pub.publish(cmd))
        executor = SingleThreadedExecutor()
        executor.add_node(bridge); executor.add_node(client)
        raw = b''
        try:
            deadline = time.monotonic()+3
            while time.monotonic() < deadline and b'm 0.05000 0.00000 0.00000\n' not in raw:
                executor.spin_once(timeout_sec=0.05)
                try: raw += os.read(master, 4096)
                except BlockingIOError: pass
            self.assertIn(b'geom 0.05000 0.15000 0.12500\n', raw)
            self.assertIn(b'm 0.05000 0.00000 0.00000\n', raw)
            state = b'STATE,1000,1,2,3,4,50,51,52,53,1\n'
            os.write(master, state)
            deadline = time.monotonic()+2
            while time.monotonic() < deadline and not received:
                executor.spin_once(timeout_sec=0.05)
            self.assertEqual(received[-1], state.decode().strip())
            timer.cancel()
            # Drop previous traffic, then allow command freshness to expire.
            stop_raw = b''
            deadline = time.monotonic()+0.9
            while time.monotonic() < deadline:
                executor.spin_once(timeout_sec=0.05)
                try: stop_raw += os.read(master, 4096)
                except BlockingIOError: pass
            self.assertTrue(stop_raw.endswith(b'stop\n'), stop_raw)
        finally:
            bridge.close(); executor.shutdown()
            bridge.destroy_node(); client.destroy_node(); rclpy.shutdown()
            os.close(master); os.close(slave)


if __name__ == '__main__':
    unittest.main()
