"""Actual ROS + PTY; checks transport, not motor motion or firmware mechanics."""
import os
import pty
import time
import unittest
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.executors import SingleThreadedExecutor
from std_msgs.msg import String
from bridge_node import DynamixelBridge

class BridgeTest(unittest.TestCase):
    def test_commands_feedback_and_shutdown(self):
        master, slave = pty.openpty(); os.set_blocking(master, False)
        rclpy.init()
        bridge = DynamixelBridge(parameter_overrides=[Parameter('dry_run', value=False),
            Parameter('serial_port', value=os.ttyname(slave)), Parameter('serial_boot_delay_sec', value=0.0)])
        client = Node('meroedu_dynamixel_test'); received = []
        client.create_subscription(String, '/dynamixel/state', lambda msg: received.append(msg.data), 10)
        pub = client.create_publisher(String, '/dynamixel/command', 10)
        executor = SingleThreadedExecutor(); executor.add_node(bridge); executor.add_node(client)
        raw = b''
        def drain(duration):
            nonlocal raw
            until = time.monotonic()+duration
            while time.monotonic() < until:
                executor.spin_once(timeout_sec=0.02)
                try: raw += os.read(master, 4096)
                except BlockingIOError: pass
        try:
            drain(0.5)
            self.assertIn(b'STOP\n', raw)
            self.assertNotIn(b'TORQUE_ON', raw)
            self.assertNotIn(b'DXL_POWER_ON', raw)
            for command in ['PING', 'MOVE_DELTA 32', 'MOVE_DELTA 65', 'MOVE_DELTA 32\nSTOP']:
                msg = String(); msg.data = command; pub.publish(msg); drain(0.2)
            self.assertIn(b'PING\n', raw)
            self.assertEqual(raw.count(b'MOVE_DELTA 32\n'), 1)
            self.assertNotIn(b'MOVE_DELTA 65', raw)
            os.write(master, b'STATE POWER=1 READY=1 TORQUE=0 POSITION=2048\n')
            drain(0.3)
            self.assertIn('STATE POWER=1 READY=1 TORQUE=0 POSITION=2048', received)
            bridge.close(); drain(0.1)
            self.assertTrue(raw.endswith(b'STOP\n'), raw)
        finally:
            bridge.close(); executor.shutdown(); bridge.destroy_node(); client.destroy_node(); rclpy.shutdown()
            os.close(master); os.close(slave)

if __name__ == '__main__': unittest.main()
