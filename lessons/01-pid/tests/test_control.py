import unittest,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pid import PID,encoder_speed,world_to_body,line_command
class ControlTest(unittest.TestCase):
    def test_speed_units_and_sign(self):
        self.assertAlmostEqual(encoder_speed(1320,1320,1),2*math.pi)
        self.assertLess(encoder_speed(-20,1320,.02),0)
    def test_saturation_does_not_wind_up(self):
        c=PID(10,8,output_limit=20)
        for _ in range(1000): self.assertEqual(c.step(100,0,.02),20)
        self.assertEqual(c.integral,0)
        self.assertEqual(c.step(0,0,.02),0)
    def test_body_rotation(self):
        x,y=world_to_body(1,0,math.pi/2)
        self.assertAlmostEqual(x,0);self.assertAlmostEqual(y,-1)
    def test_line_converges_without_disturbance(self):
        c=PID(2.5,output_limit=.45);y=.18
        for _ in range(500):
            _,vy=line_command(y,0,c,.02);y+=vy*.02
        self.assertLess(abs(y),.006)
    def test_invalid_time(self):
        with self.assertRaises(ValueError):PID(1).step(1,0,0)
if __name__=='__main__':unittest.main()
