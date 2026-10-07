"""Tyre pressure monitoring - the capstone system under test.

Specification (all pressures in kPa, temperatures in degC)
  S1  Pressure is normalised to 20 degC:  p20 = p * 293.15 / (273.15 + temp)
  S2  Nominal pressure is 230 kPa.
  S3  p20 <  60 % of nominal                     -> CRITICAL
  S4  60 % <= p20 < 80 % of nominal              -> LOW
  S5  80 % <= p20 <= 130 % of nominal            -> OK
  S6  p20 > 130 % of nominal                     -> HIGH
  S7  A drop of >= 20 kPa within a 60 s window   -> rapid loss (leak) alarm
  S8  Sensor ids are exactly 8 hex digits (either case); anything else is rejected with
      ValueError. Valid ids are returned in UPPER case.
  S9  Readings outside 0..700 kPa or -40..125 degC are rejected with ValueError.
"""
from __future__ import annotations

import enum
import re
from collections import deque

NOMINAL_KPA = 230.0


class TyreStatus(enum.Enum):
    CRITICAL = "critical"
    LOW = "low"
    OK = "ok"
    HIGH = "high"


def normalise_pressure(kpa: float, temp_c: float) -> float:
    return kpa * 293.15 / (273.15 + temp_c)


def classify(kpa: float, temp_c: float, nominal: float = NOMINAL_KPA) -> TyreStatus:
    if not 0 <= kpa <= 700 or not -40 <= temp_c <= 125:
        raise ValueError("reading out of sensor range")
    p20 = normalise_pressure(kpa, temp_c)
    if p20 < 0.6 * nominal:
        return TyreStatus.CRITICAL
    if p20 < 0.8 * nominal:
        return TyreStatus.LOW
    if p20 <= 1.3 * nominal:
        return TyreStatus.OK
    return TyreStatus.HIGH


_SENSOR_ID = re.compile(r"[0-9A-Fa-f]{8}")


def validate_sensor_id(sensor_id: str) -> str:
    if not _SENSOR_ID.fullmatch(sensor_id):
        raise ValueError(f"bad sensor id {sensor_id!r}")
    return sensor_id.upper()


class LeakDetector:
    WINDOW_S = 60.0
    DROP_KPA = 20.0

    def __init__(self) -> None:
        self._samples: deque[tuple[float, float]] = deque()

    def add(self, t: float, kpa: float) -> bool:
        """Record a sample, return True when a rapid loss is detected."""
        self._samples.append((t, kpa))
        while self._samples and t - self._samples[0][0] > self.WINDOW_S:
            self._samples.popleft()
        highest = max(p for _, p in self._samples)
        return highest - kpa >= self.DROP_KPA
