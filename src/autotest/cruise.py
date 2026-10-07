"""Adaptive-free cruise control: mode state machine plus a PI speed controller."""
from __future__ import annotations

import enum


class CruiseState(enum.Enum):
    OFF = "off"
    STANDBY = "standby"
    ACTIVE = "active"
    OVERRIDE = "override"  # driver is pressing the accelerator


class CruiseController:
    MIN_SET_SPEED = 30.0   # km/h
    MAX_SET_SPEED = 180.0  # km/h

    def __init__(self, kp: float = 0.05, ki: float = 0.01):
        self.kp, self.ki = kp, ki
        self.state = CruiseState.OFF
        self.target: float | None = None
        self.saved_target: float | None = None
        self._integral = 0.0

    # --- driver inputs -------------------------------------------------
    def power_on(self) -> None:
        if self.state is CruiseState.OFF:
            self.state = CruiseState.STANDBY

    def power_off(self) -> None:
        self.state = CruiseState.OFF
        self.target = self.saved_target = None
        self._integral = 0.0

    def set(self, speed_kmh: float) -> bool:
        """Engage / change the set speed. Returns False if the request is refused."""
        if self.state is CruiseState.OFF:
            return False
        if not self.MIN_SET_SPEED <= speed_kmh <= self.MAX_SET_SPEED:
            return False
        self.target = speed_kmh
        self.saved_target = speed_kmh
        self.state = CruiseState.ACTIVE
        self._integral = 0.0
        return True

    def resume(self, current_speed_kmh: float) -> bool:
        if self.state is not CruiseState.STANDBY or self.saved_target is None:
            return False
        if current_speed_kmh < self.MIN_SET_SPEED:
            return False
        return self.set(self.saved_target)

    def cancel(self) -> None:
        if self.state in (CruiseState.ACTIVE, CruiseState.OVERRIDE):
            self.saved_target = self.target
            self.target = None
            self.state = CruiseState.STANDBY
            self._integral = 0.0

    brake = cancel  # pressing the brake pedal always cancels

    def accelerator(self, pressed: bool) -> None:
        if pressed and self.state is CruiseState.ACTIVE:
            self.state = CruiseState.OVERRIDE
        elif not pressed and self.state is CruiseState.OVERRIDE:
            self.state = CruiseState.ACTIVE
            self._integral = 0.0

    # --- control law ----------------------------------------------------
    def control(self, speed_kmh: float, dt: float) -> float:
        """Throttle request 0..1. Zero unless ACTIVE."""
        if self.state is not CruiseState.ACTIVE or self.target is None:
            return 0.0
        error = self.target - speed_kmh
        unsat = self.kp * error + self.ki * (self._integral + error * dt)
        out = min(1.0, max(0.0, unsat))
        if out == unsat:  # anti-windup: only integrate while not saturated
            self._integral += error * dt
        return out
