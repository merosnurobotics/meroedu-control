import math
import unittest
from protocol import CommandGate, body_to_wheels, limit_twist, parse_state


class ProtocolTest(unittest.TestCase):
    def test_forward_and_sideways_axes(self):
        self.assertEqual(body_to_wheels(0.1, 0, 0, 0.05, 0.15, 0.125), (2, 2, 2, 2))
        self.assertEqual(body_to_wheels(0, 0.1, 0, 0.05, 0.15, 0.125), (-2, 2, 2, -2))

    def test_combined_speed_limit_preserves_direction(self):
        original = (0.15, 0.15, 0.5)
        limited = limit_twist(*original, 0.05, 0.15, 0.125)
        wheels = body_to_wheels(*limited, 0.05, 0.15, 0.125)
        self.assertLessEqual(max(map(abs, wheels)), 6.000001)
        self.assertAlmostEqual(limited[0]/original[0], limited[2]/original[2])

    def test_timeout_and_invalid_command(self):
        gate = CommandGate()
        self.assertEqual(gate.line(0), 'stop\n')
        gate.accept(0.05, 0, 0, 10)
        self.assertEqual(gate.line(10.1), 'm 0.05000 0.00000 0.00000\n')
        self.assertEqual(gate.line(10.6), 'stop\n')
        with self.assertRaises(ValueError):
            gate.accept(math.nan, 0, 0, 11)
        self.assertEqual(gate.line(11), 'stop\n')

    def test_state_contract(self):
        state = parse_state('STATE,1000,1,2,3,4,50,51,52,53,1')
        self.assertEqual(state['ticks'], [1, 2, 3, 4])
        self.assertEqual(state['pwm'], [50, 51, 52, 53])
        self.assertIsNone(parse_state('STATE,1,2'))
        self.assertIsNone(parse_state('READY encoder_motor'))


if __name__ == '__main__':
    unittest.main()
