import unittest
from protocol import command_line

class ProtocolTest(unittest.TestCase):
    def test_movement_bounds_and_injection(self):
        self.assertEqual(command_line('MOVE_DELTA -64'), 'MOVE_DELTA -64\n')
        self.assertEqual(command_line('PING'), 'PING\n')
        for value in ['MOVE_DELTA 65', 'MOVE_DELTA 0', 'MOVE_DELTA nan', 'MOVE_DELTA 32\nSTOP', 'REBOOT', 'INIT\r']:
            with self.subTest(value=value):
                with self.assertRaises(ValueError): command_line(value)

if __name__ == '__main__': unittest.main()
