"""Lab 7 exercises. Run: pytest labs/lab07_property_based/exercise_lab07.py -v"""
import pytest
from hypothesis import given, strategies as st

from autotest.abs import slip_ratio
from autotest.diagnostics import DiagnosticManager


# Exercise 1 - properties of slip_ratio: (a) always within [0, 1], (b) 0 when wheel == vehicle,
# (c) 1 when the wheel is stopped and the car is moving > 0.5 m/s. Write one @given test each.
def test_slip_properties():
    pytest.fail("TODO")


# Exercise 2 - Stateful thinking: generate lists of booleans (st.lists(st.booleans())) as DTC
# pass/fail histories. Property: a code is active iff the LAST `fail_threshold` results are all
# failures OR (it was active before and fewer than `heal_threshold` passes followed).
# Write a tiny reference model in the test and compare it with DiagnosticManager.
def test_dtc_matches_reference_model():
    pytest.fail("TODO")


# Exercise 3 - Custom strategy: build st.builds(CANFrame, ...) with valid ids, then assert
# that e2e_protect(frame.data[:6], 3) is always a valid input for e2e_check.
def test_custom_strategy():
    pytest.fail("TODO")
