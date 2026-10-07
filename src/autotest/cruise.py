"""Cruise control: a mode state machine (OFF/STANDBY/ACTIVE/OVERRIDE) plus a PI speed controller.

Speeds in km/h, time in s, throttle request in 0..1. Driver inputs are methods; `control()`
is the periodic control task that turns speed error into a throttle request.
"""
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
        """OFF -> STANDBY (ignored in any other state)."""
        if self.state is CruiseState.OFF:
            self.state = CruiseState.STANDBY

    def power_off(self) -> None:
        """Any state -> OFF, forgetting both the target and the saved target."""
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
        """STANDBY -> ACTIVE at the saved target; refused without one or below the minimum speed."""
        if self.state is not CruiseState.STANDBY or self.saved_target is None:
            return False
        if current_speed_kmh < self.MIN_SET_SPEED:
            return False
        return self.set(self.saved_target)

    def cancel(self) -> None:
        """ACTIVE/OVERRIDE -> STANDBY, remembering the target so `resume` can restore it."""
        if self.state in (CruiseState.ACTIVE, CruiseState.OVERRIDE):
            self.saved_target = self.target
            self.target = None
            self.state = CruiseState.STANDBY
            self._integral = 0.0

    brake = cancel  # pressing the brake pedal always cancels

    def accelerator(self, pressed: bool) -> None:
        """Driver override: pressing in ACTIVE -> OVERRIDE; releasing in OVERRIDE -> ACTIVE."""
        if pressed and self.state is CruiseState.ACTIVE:
            self.state = CruiseState.OVERRIDE
        elif not pressed and self.state is CruiseState.OVERRIDE:
            self.state = CruiseState.ACTIVE
            self._integral = 0.0

    # --- control law ----------------------------------------------------
    def control(self, speed_kmh: float, dt: float) -> float:
        """Throttle request 0..1. Zero unless ACTIVE.

        PI law:  u = Kp*e + Ki*(integral of e).  The result is clamped to 0..1, and the integral is
        only updated while the output is NOT clamped (conditional integration = anti-windup).
        """
        if self.state is not CruiseState.ACTIVE or self.target is None:
            return 0.0
        error = self.target - speed_kmh                              # km/h, positive = too slow
        unsaturated = self.kp * error + self.ki * (self._integral + error * dt)
        output = min(1.0, max(0.0, unsaturated))
        if output == unsaturated:                                    # not saturated: safe to integrate
            self._integral += error * dt
        return output
