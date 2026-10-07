"""Sensor conversions and a plausibility-checked temperature sensor."""
from __future__ import annotations

from collections import deque
from typing import Protocol


class SensorFault(Exception):
    """Raised when a raw reading is physically implausible."""


def kmh_to_ms(kmh: float) -> float:
    return kmh / 3.6


def ms_to_kmh(ms: float) -> float:
    return ms * 3.6


def celsius_to_fahrenheit(c: float) -> float:
    return c * 9 / 5 + 32


def wheel_speed_kmh(pulses: int, pulses_per_rev: int, circumference_m: float, interval_s: float) -> float:
    """Speed from a toothed-wheel sensor: pulses counted during `interval_s` seconds -> km/h."""
    if pulses < 0 or pulses_per_rev <= 0 or circumference_m <= 0 or interval_s <= 0:
        raise ValueError(
            f"invalid wheel speed parameters: pulses={pulses}, pulses_per_rev={pulses_per_rev}, "
            f"circumference_m={circumference_m}, interval_s={interval_s} (all must be positive; pulses may be 0)"
        )
    revs_per_s = pulses / pulses_per_rev / interval_s
    return ms_to_kmh(revs_per_s * circumference_m)


class ADC(Protocol):
    """Hardware abstraction: real boards, simulators and mocks all fit this."""

    def read(self) -> int: ...


class TemperatureSensor:
    """12-bit ADC mapped linearly to -40..150 degC. Rail values mean a wiring fault."""

    ADC_MAX = 4095
    T_MIN, T_MAX = -40.0, 150.0

    def __init__(self, adc: ADC, filter_len: int = 4):
        if filter_len < 1:
            raise ValueError(f"filter_len must be >= 1, got {filter_len}")
        self._adc = adc
        self._window: deque[float] = deque(maxlen=filter_len)

    def read(self) -> float:
        """One conversion -> degC. Raises SensorFault if the ADC sits at either rail (wiring fault)."""
        counts = self._adc.read()
        if counts <= 0:
            raise SensorFault("short to ground")
        if counts >= self.ADC_MAX:
            raise SensorFault("open circuit / short to supply")
        return self.T_MIN + (self.T_MAX - self.T_MIN) * counts / self.ADC_MAX

    def read_filtered(self) -> float:
        """Moving average of the last `filter_len` good readings (a faulty read leaves the window untouched)."""
        self._window.append(self.read())
        return sum(self._window) / len(self._window)
