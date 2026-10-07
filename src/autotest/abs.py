"""ABS slip controller and a quarter-car plant for software-in-the-loop tests.

The plant is ONE wheel carrying a quarter of the car. Speeds are in m/s, force in N,
torque in Nm, pressure is a fraction 0..1 of the maximum brake pressure.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass

G = 9.81


class Valve(enum.Enum):
    """What the hydraulic modulator does to the brake pressure."""

    APPLY = "apply"
    HOLD = "hold"
    RELEASE = "release"


def slip_ratio(vehicle_ms: float, wheel_ms: float) -> float:
    """0 = free rolling, 1 = locked wheel. Undefined (0) at standstill."""
    if vehicle_ms <= 0.5:
        return 0.0
    return min(1.0, max(0.0, (vehicle_ms - wheel_ms) / vehicle_ms))


class ABSController:
    """Three-state bang-bang slip controller with a hysteresis band between the two limits."""

    RELEASE_ABOVE = 0.25
    APPLY_BELOW = 0.15
    MIN_ACTIVE_SPEED = 5.0  # m/s - ABS is disabled below this

    def decide(self, vehicle_ms: float, wheel_ms: float) -> Valve:
        if vehicle_ms < self.MIN_ACTIVE_SPEED:
            return Valve.APPLY
        s = slip_ratio(vehicle_ms, wheel_ms)
        if s > self.RELEASE_ABOVE:
            return Valve.RELEASE
        if s < self.APPLY_BELOW:
            return Valve.APPLY
        return Valve.HOLD


def tyre_mu(slip: float) -> float:
    """Simplified friction curve: peak 1.0 at 20 % slip, 0.7 when locked."""
    if slip <= 0.2:
        return slip / 0.2
    return 1.0 - 0.3 * (slip - 0.2) / 0.8


@dataclass
class QuarterCar:
    speed_ms: float = 27.8      # ~100 km/h
    wheel_ms: float = 27.8
    pressure: float = 0.0       # 0..1
    distance_m: float = 0.0
    mass: float = 400.0
    radius: float = 0.3
    inertia: float = 1.5
    max_brake_torque: float = 2000.0

    def step(self, dt: float, valve: Valve) -> None:
        """Advance the physics by `dt` seconds (explicit Euler) under the valve command."""
        # 1. Hydraulics: the valve changes brake pressure at a fixed rate (per second).
        rate = {Valve.APPLY: 10.0, Valve.HOLD: 0.0, Valve.RELEASE: -40.0}[valve]
        self.pressure = min(1.0, max(0.0, self.pressure + rate * dt))

        # 2. Tyre: slip decides how much of the normal force becomes braking force.
        mu = tyre_mu(slip_ratio(self.speed_ms, self.wheel_ms))
        force = mu * self.mass * G                                   # N, decelerates the car

        # 3. Wheel: the road force spins the wheel UP, the brake torque slows it DOWN.
        wheel_omega = self.wheel_ms / self.radius                    # rad/s
        brake_torque = self.pressure * self.max_brake_torque if wheel_omega > 0 else 0.0
        wheel_omega += (force * self.radius - brake_torque) / self.inertia * dt
        wheel_omega = max(0.0, wheel_omega)                          # a wheel cannot spin backwards here
        if self.speed_ms <= 0.5 and wheel_omega * self.radius > self.speed_ms:
            wheel_omega = self.speed_ms / self.radius                # standing car: wheel cannot outrun it
        self.wheel_ms = wheel_omega * self.radius

        # 4. Vehicle: integrate speed and distance.
        self.speed_ms = max(0.0, self.speed_ms - force / self.mass * dt)
        self.distance_m += self.speed_ms * dt


def simulate_braking(use_abs: bool, dt: float = 0.001, t_max: float = 15.0) -> dict:
    """Brake from ~100 km/h to a stop. Returns distance_m, time_s, peak_slip, locked_s.

    peak_slip and locked_s are only measured while ABS is allowed to act (speed >= 5 m/s).
    """
    car, ctrl = QuarterCar(), ABSController()
    t, peak_slip, locked_time = 0.0, 0.0, 0.0
    while car.speed_ms > 0.5 and t < t_max:
        valve = ctrl.decide(car.speed_ms, car.wheel_ms) if use_abs else Valve.APPLY
        car.step(dt, valve)
        if car.speed_ms >= ABSController.MIN_ACTIVE_SPEED:  # below this ABS is off by design
            s = slip_ratio(car.speed_ms, car.wheel_ms)
            peak_slip = max(peak_slip, s)
            if s > 0.95:
                locked_time += dt
        t += dt
    return {"distance_m": car.distance_m, "time_s": t, "peak_slip": peak_slip, "locked_s": locked_time}
