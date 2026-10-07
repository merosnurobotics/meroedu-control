"""Toy plants, not hardware measurements; save time series for plotting."""
import argparse, csv, math
from pathlib import Path
from pid import PID, encoder_speed, line_command

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, default=Path('output'))
args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
dt = .02
for mode, gains in [('p',(10.,0.,0.)), ('pi',(10.,8.,0.)), ('pid',(10.,8.,.2))]:
    controller=PID(*gains); speed=0.; angle=0.; old_ticks=0; rows=[]
    for k in range(1000):
        t=k*dt; target=5. if t>=1 else 0.
        ticks=round(angle/(2*math.pi)*1320)
        measured=encoder_speed(ticks-old_ticks,1320,dt); old_ticks=ticks
        if target==0: controller.reset(); pwm=0.
        else: pwm=controller.step(target,measured,dt,feedforward=10+6.9*target)
        # Simple first-order motor, load changes at 6s; gains are educational.
        load=15. if t>=6 else 0.
        equilibrium=max(0.,(pwm-10-load)/6.9)
        speed += (equilibrium-speed)*dt/.3
        angle += speed*dt
        rows.append((t,target,measured,pwm))
    with (args.output/f'motor-{mode}.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['t_s','target_rad_s','measured_rad_s','pwm']);w.writerows(rows)
controller=PID(2.5,output_limit=.45); x=0.; y=.18; rows=[]
for k in range(500):
    t=k*dt; vx,vy=line_command(y,0.,controller,dt)
    disturbance=.035 if t>=4 else 0.
    x+=vx*dt; y+=(vy+disturbance)*dt
    rows.append((t,x,y,vx,vy))
with (args.output/'line.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['t_s','x_m','y_m','vx_m_s','vy_m_s']);w.writerows(rows)
print('Saved motor-p/pi/pid.csv and line.csv; simulated, not real robot data.')
