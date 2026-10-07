"""Solutions - Lab 8 (robustness)."""
import math

import pytest

from autotest.bms import BatteryManagementSystem, max_charge_current
from autotest.bus import VirtualCANBus
from autotest.ecu import DTC_COMM_LOST, InstrumentCluster, WheelSpeedECU
from autotest.sensors import SensorFault, TemperatureSensor

pytestmark = pytest.mark.robustness


# 1 - The production fix is in bms_nan_fix.patch (apply it, then delete the two xfail markers).
#     Here we prove the *design* of the fix with a guard wrapper so this suite stays green
#     while the strict-xfail demo tests in Lab 8 remain valid.
def guarded_max_charge_current(soc, temp):
    if math.isnan(temp):
        raise ValueError("temperature is not a number")
    return max_charge_current(soc, temp)


def test_guarded_function_rejects_nan_temperature():
    with pytest.raises(ValueError):
        guarded_max_charge_current(50, math.nan)


# 2 - stuck-value plausibility check (TDD: this test was written first)
class StuckAwareSensor(TemperatureSensor):
    STUCK_AFTER = 100

    def __init__(self, adc, filter_len=4):
        super().__init__(adc, filter_len)
        self._last, self._same = None, 0

    def read(self):
        value = super().read()
        self._same = self._same + 1 if value == self._last else 0
        self._last = value
        if self._same >= self.STUCK_AFTER:
            raise SensorFault("stuck")
        return value


class Ramp:
    def __init__(self):
        self.n = 1000

    def read(self):
        self.n += 1
        return self.n


class Const:
    def read(self):
        return 2000


def test_stuck_sensor_detected():
    sensor = StuckAwareSensor(Const())
    with pytest.raises(SensorFault, match="stuck"):
        for _ in range(200):
            sensor.read()


def test_moving_sensor_is_not_flagged():
    sensor = StuckAwareSensor(Ramp())
    for _ in range(500):
        sensor.read()


# 3 - burst error: five consecutive frames lost
def test_burst_loss_and_recovery(bus, clock):
    ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)
    ecu.send_speed(50)
    assert cluster.displayed_speed() == "50"

    lost = {"n": 0}

    def drop_five(frame):
        lost["n"] += 1
        return None if lost["n"] <= 5 else frame

    bus.add_fault(drop_five)
    for _ in range(5):
        ecu.send_speed(51)
        clock.advance(0.03)
    assert cluster.displayed_speed() == "--"             # 150 ms of silence -> blank
    cluster.displayed_speed()
    assert cluster.diag.active_codes() == [DTC_COMM_LOST]

    shown = []
    for _ in range(3):                                   # first frame after the burst is a counter
        ecu.send_speed(60)                               # error (resync), then normal service
        shown.append(cluster.displayed_speed())
    assert shown[-1] == "60"
    assert DTC_COMM_LOST in cluster.diag.stored_codes()  # history is retained after recovery
