"""Lab 8 exercises - robustness: fix real bugs, TDD a safety check, model a burst error.

  Run it:       python course.py exercise 8
  How it works: Exercise 1 asserts the SAFE behaviour and fails because of a real bug in src/ - fix the code.
                Exercises 2 and 3 start with todo(...) lines: delete them when you start on the test.
  Done when:    `python course.py progress` shows every test of Lab 8 passing.
"""
import math

import pytest

from autotest.bms import BatteryManagementSystem, BMSFault, max_charge_current
from autotest.bus import VirtualCANBus
from autotest.ecu import InstrumentCluster, WheelSpeedECU
from autotest.learn import todo
from autotest.sensors import SensorFault, TemperatureSensor


# --------------------------------------------------------------------------------------------------
# Exercise 1 - FIX TWO REAL DEFECTS in src/autotest/bms.py.
# These tests are already written and fail today. They describe the FAIL-SAFE behaviour: an unknown
# (NaN) input must never be treated as "OK".
# Hint 1: every comparison with NaN is False, so `temp_c < 0 or temp_c > 45` lets NaN through.
# Hint 2: math.isnan(x) detects it. Reject the input with ValueError (or return the most restrictive result).
# Afterwards: open test_lab08_robustness.py, delete the two xfail(strict=True) markers (they now go RED
# on purpose - a strict xfail that passes is a failure: it forces you to clean up) and run the whole suite.
# --------------------------------------------------------------------------------------------------
def test_nan_temperature_must_not_allow_charging():
    try:
        current = max_charge_current(50, math.nan)
    except ValueError:                 # rejecting the input is as safe as returning 0 A
        return
    assert current == 0.0, "an unknown temperature must never allow charging"


def test_nan_cell_voltage_must_not_report_healthy():
    try:
        fault = BatteryManagementSystem().evaluate([3.7, math.nan, 3.7], 25)
    except ValueError:
        return
    assert fault is not BMSFault.NONE, "an unknown cell voltage must never be reported as healthy"


# --------------------------------------------------------------------------------------------------
# Exercise 2 - TDD: a stuck sensor must be detected. Write the tests FIRST, then implement the check.
# --------------------------------------------------------------------------------------------------
class ConstADC:
    def read(self):
        return 2000


class Ramp:
    """An ADC whose value changes with every read - a healthy, moving signal."""

    def __init__(self):
        self.n = 1000

    def read(self):
        self.n += 1
        return self.n


class StuckAwareSensor(TemperatureSensor):
    """A TemperatureSensor that raises SensorFault('stuck') after 100 identical readings in a row."""

    def read(self):
        todo("implement: call super().read(), count identical values, raise SensorFault('stuck') at 100")


def test_stuck_sensor_is_detected():
    """Hint: with pytest.raises(SensorFault, match="stuck"):  read 200 times from StuckAwareSensor(ConstADC())"""
    todo("write the test (then make it pass by implementing StuckAwareSensor.read)")


def test_a_moving_sensor_is_not_flagged():
    """Hint: the same loop with Ramp() must NOT raise. (A check that fires on healthy data is a defect too.)"""
    todo("write the test")


# --------------------------------------------------------------------------------------------------
# Exercise 3 - a BURST ERROR: five consecutive frames lost.
# --------------------------------------------------------------------------------------------------
def test_burst_loss_and_recovery(bus, clock):
    """Show that (1) the cluster blanks during the silence, (2) it shows numbers again after the burst,
    (3) the 'communication lost' DTC (U0121) is still STORED afterwards.

    Hint 1: ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock);  send one good frame first.
    Hint 2: a hook that drops the first five frames:  state = {"n": 0};  def drop_five(frame): state["n"] += 1; return None if state["n"] <= 5 else frame
    Hint 3: send 5 frames while advancing clock.advance(0.03) each; then cluster.displayed_speed() == "--" (twice, DTC debouncing needs 2 misses).
    Hint 4: afterwards send a few more frames; the first one after the burst is rejected by the alive counter (a resync),
            so check the display after 2-3 frames. Finally: "U0121" in cluster.diag.stored_codes().
    """
    todo("write the burst-loss scenario")
