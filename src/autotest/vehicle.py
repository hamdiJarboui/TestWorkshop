"""Longitudinal vehicle model (point mass + drag + rolling resistance + grade)."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .cruise import CruiseController

G = 9.81


@dataclass
class Vehicle:
    speed_ms: float = 0.0
    mass: float = 1500.0
    max_drive_force: float = 2500.0   # N at full throttle
    cd_a: float = 0.66                # drag coefficient x frontal area (m^2)
    crr: float = 0.01                 # rolling resistance coefficient
    rho: float = 1.2                  # air density

    def step(self, throttle: float, dt: float, grade: float = 0.0, brake_force: float = 0.0) -> float:
        throttle = min(1.0, max(0.0, throttle))
        drag = 0.5 * self.rho * self.cd_a * self.speed_ms ** 2
        rolling = self.crr * self.mass * G if self.speed_ms > 0 else 0.0
        slope = self.mass * G * math.sin(math.atan(grade))
        net = throttle * self.max_drive_force - drag - rolling - slope - brake_force
        self.speed_ms = max(0.0, self.speed_ms + net / self.mass * dt)
        return self.speed_ms * 3.6

    @property
    def speed_kmh(self) -> float:
        return self.speed_ms * 3.6


def run_cruise(cc: CruiseController, start_kmh: float, duration_s: float, dt: float = 0.1,
               grade_profile=lambda t: 0.0, events=None):
    """Closed-loop simulation. `events` maps time (s) -> callable(cc, vehicle)."""
    car = Vehicle(speed_ms=start_kmh / 3.6)
    events = dict(events or {})
    trace = []
    for k in range(int(duration_s / dt)):
        t = round(k * dt, 6)
        if t in events:
            events[t](cc, car)
        throttle = cc.control(car.speed_kmh, dt)
        car.step(throttle, dt, grade_profile(t))
        trace.append((t, car.speed_kmh, throttle))
    return trace
