"""Velocity-only serial helpers. Wheel order: FL, FR, RL, RR; SI units."""
import math
from dataclasses import dataclass


def body_to_wheels(vx, vy, wz, radius, half_length, half_width):
    if not all(math.isfinite(x) for x in (vx, vy, wz, radius, half_length, half_width)):
        raise ValueError('All commands and geometry must be finite')
    if radius <= 0 or min(half_length, half_width) <= 0:
        raise ValueError('Geometry must be positive')
    k = half_length + half_width
    return ((vx-vy-k*wz)/radius, (vx+vy+k*wz)/radius,
            (vx+vy-k*wz)/radius, (vx-vy+k*wz)/radius)


def limit_twist(vx, vy, wz, radius, half_length, half_width, max_wheel_rad_s=6.0):
    if not math.isfinite(max_wheel_rad_s) or max_wheel_rad_s <= 0:
        raise ValueError('Positive wheel speed limit required')
    wheels = body_to_wheels(vx, vy, wz, radius, half_length, half_width)
    scale = max(1.0, max(abs(w) for w in wheels)/max_wheel_rad_s)
    return tuple(v/scale for v in (vx, vy, wz))


@dataclass
class CommandGate:
    timeout_sec: float = 0.5
    received_at: float | None = None
    target: tuple = (0.0, 0.0, 0.0)

    def accept(self, vx, vy, wz, now):
        if not all(math.isfinite(v) for v in (vx, vy, wz, now)):
            self.received_at = None
            self.target = (0.0, 0.0, 0.0)
            raise ValueError('Invalid velocity; clear previous command')
        self.target, self.received_at = (vx, vy, wz), now

    def line(self, now):
        if self.received_at is None or now-self.received_at > self.timeout_sec:
            return 'stop\n'
        return 'm {:.5f} {:.5f} {:.5f}\n'.format(*self.target)


def parse_state(line):
    parts = line.strip().split(',')
    if len(parts) != 11 or parts[0] != 'STATE':
        return None
    try:
        values = [int(v) for v in parts[1:]]
    except ValueError:
        return None
    return {'device_ms': values[0], 'ticks': values[1:5], 'pwm': values[5:9], 'mode': values[9]}
