"""Battery management: charge-current derating, protection and SOC."""
from __future__ import annotations

import enum


class BMSFault(enum.Enum):
    NONE = "none"
    OVERVOLTAGE = "overvoltage"
    UNDERVOLTAGE = "undervoltage"
    OVERTEMPERATURE = "overtemperature"
    UNDERTEMPERATURE = "undertemperature"


def max_charge_current(soc: float, temp_c: float, rated_a: float = 100.0) -> float:
    """Allowed charge current (A).

    Decision table (see Lab 3):
      temp < 0 or temp > 45   -> 0 A   (lithium plating / thermal risk)
      0 <= temp < 10          -> 25 % of rated
      10 <= temp <= 45        -> 100 % of rated
      soc >= 100              -> 0 A
      soc > 80                -> taper linearly from the temperature limit to 0 at 100 %
    """
    if not 0 <= soc <= 100:
        raise ValueError("soc must be within 0..100")
    if temp_c < 0 or temp_c > 45:
        return 0.0
    limit = rated_a * (0.25 if temp_c < 10 else 1.0)
    if soc >= 100:
        return 0.0
    if soc > 80:
        limit *= (100 - soc) / 20
    return limit


class BatteryManagementSystem:
    CELL_V_MAX = 4.20
    CELL_V_MIN = 3.00
    TEMP_MAX = 60.0
    TEMP_MIN = -20.0

    def __init__(self, capacity_ah: float = 50.0, soc: float = 50.0):
        if capacity_ah <= 0:
            raise ValueError("capacity must be positive")
        self.capacity_ah = capacity_ah
        self.soc = soc

    def evaluate(self, cell_voltages: list[float], temp_c: float) -> BMSFault:
        if not cell_voltages:
            raise ValueError("no cell data")
        if max(cell_voltages) > self.CELL_V_MAX:
            return BMSFault.OVERVOLTAGE
        if min(cell_voltages) < self.CELL_V_MIN:
            return BMSFault.UNDERVOLTAGE
        if temp_c > self.TEMP_MAX:
            return BMSFault.OVERTEMPERATURE
        if temp_c < self.TEMP_MIN:
            return BMSFault.UNDERTEMPERATURE
        return BMSFault.NONE

    def update_soc(self, current_a: float, dt_s: float) -> float:
        """Coulomb counting. Positive current charges the pack."""
        if dt_s < 0:
            raise ValueError("dt must be >= 0")
        delta = current_a * dt_s / 3600 / self.capacity_ah * 100
        self.soc = min(100.0, max(0.0, self.soc + delta))
        return self.soc
