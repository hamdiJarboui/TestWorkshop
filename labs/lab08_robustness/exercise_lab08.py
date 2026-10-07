"""Lab 8 exercises. Run: pytest labs/lab08_robustness/exercise_lab08.py -v"""
import pytest


# Exercise 1 - FIX BUG-201 and BUG-202 in src/autotest/bms.py (reject NaN with ValueError).
# Then REMOVE the xfail markers in test_lab08_robustness.py and watch the suite stay green.
# (strict xfail goes RED when the bug is fixed - that is the feature: it forces cleanup.)
def test_bugs_fixed():
    pytest.fail("TODO: make the two strict-xfail tests pass for real")


# Exercise 2 - Add a plausibility check to TemperatureSensor.read_filtered: a value that does
# not change AT ALL for 100 consecutive reads raises SensorFault('stuck'). Write the failing
# test first (TDD), then implement.
def test_stuck_sensor_detected():
    pytest.fail("TODO")


# Exercise 3 - Write a fault hook for VirtualCANBus that models a *burst error*: 5 consecutive
# frames lost. Show the cluster blanks the display and later recovers, and that the DTC history
# is retained. Use FakeClock - no sleeping.
def test_burst_loss_and_recovery(bus, clock):
    pytest.fail("TODO")
