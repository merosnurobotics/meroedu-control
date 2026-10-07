"""Educational PID + encoder conversion; Team 14-inspired, MIT."""
import math
from dataclasses import dataclass

def clamp(value, limit):
    return max(-limit, min(limit, value))

def encoder_speed(delta_ticks, counts_per_wheel_rev, dt):
    if dt <= 0 or counts_per_wheel_rev <= 0:
        raise ValueError('dt and calibrated CPR must be positive')
    return delta_ticks * 2*math.pi / counts_per_wheel_rev / dt

@dataclass
class PID:
    kp: float
    ki: float = 0.
    kd: float = 0.
    output_limit: float = 250.
    integral_limit: float = 20.
    integral: float = 0.
    last_error: float | None = None

    def reset(self):
        self.integral = 0.
        self.last_error = None

    def step(self, target, measured, dt, feedforward=0.):
        if dt <= 0:
            raise ValueError('dt must be positive')
        error = target - measured
        candidate = clamp(self.integral + error*dt, self.integral_limit)
        derivative = 0. if self.last_error is None else (error-self.last_error)/dt
        raw = feedforward + self.kp*error + self.ki*candidate + self.kd*derivative
        # Conditional integration: do not wind up farther into saturation.
        if abs(raw) <= self.output_limit or raw*error < 0:
            self.integral = candidate
        self.last_error = error
        return clamp(feedforward + self.kp*error + self.ki*self.integral + self.kd*derivative, self.output_limit)

def world_to_body(vx, vy, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return c*vx+s*vy, -s*vx+c*vy

def line_command(y, yaw, controller, dt, reference_y=0., forward=.25):
    """Mecanum follows horizontal map line. P default (Ki=Kd=0), as upstream.
    Differential-drive robots cannot execute sideways velocity directly.
    """
    error = reference_y-y
    deadband = .005
    adjusted = math.copysign(max(0.,abs(error)-deadband),error)
    vy = controller.step(adjusted, 0., dt)
    scale = max(0., min(1., (.12-abs(error))/.08))
    return world_to_body(forward*scale, vy, yaw)
