"""Lab 7 exercises - properties with Hypothesis.

  Run it:       python course.py exercise 7
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the
                test; the test then passes only if what you wrote is correct.
  Done when:    `python course.py progress` shows every test of Lab 7 passing.

Hypothesis crash course: @given(strategy, ...) generates many inputs for the test arguments.
  st.floats(min_value=0.6, max_value=100)   st.lists(st.booleans(), max_size=40)   st.integers(1, 4)
"""
from hypothesis import given, strategies as st

from autotest.abs import slip_ratio
from autotest.can import CANFrame, E2EStatus, e2e_check, e2e_protect
from autotest.diagnostics import DiagnosticManager
from autotest.learn import todo

speeds = st.floats(min_value=0, max_value=100, allow_nan=False)


@given(speeds, speeds)
def test_slip_is_always_between_0_and_1(vehicle, wheel):
    """Exercise 1a - property: whatever the two speeds are, slip_ratio(vehicle, wheel) is within [0, 1].
    Hint: assert 0.0 <= slip_ratio(vehicle, wheel) <= 1.0
    """
    todo("assert the range property")


def test_free_rolling_has_no_slip():
    """Exercise 1b - property: if the wheel runs as fast as the car, slip is 0 (for speeds above 0.5 m/s).
    Hint: add the decorator  @given(st.floats(min_value=0.6, max_value=100))  and an argument `v`.
    """
    todo("write the property: slip_ratio(v, v) == 0")


def test_locked_wheel_is_full_slip():
    """Exercise 1c - property: a stopped wheel (0 m/s) on a moving car (> 0.5 m/s) is slip 1.
    Hint: same decorator as 1b;  assert slip_ratio(v, 0.0) == 1.0
    """
    todo("write the property: slip_ratio(v, 0) == 1")


def test_dtc_matches_reference_model():
    """Exercise 2 - a REFERENCE MODEL. Generate pass/fail histories and compare DiagnosticManager with a ten-line model
    of the SPEC: a code becomes active+stored after `fail_n` CONSECUTIVE failures, and stops being active after `heal_n`
    consecutive passes (it stays stored).

    Hint 1: decorate with  @given(st.lists(st.booleans(), max_size=40), st.integers(1, 4), st.integers(1, 4))
            and take arguments (history, fail_n, heal_n).
    Hint 2: model: keep two counters (fails, passes) and two flags (active, stored); loop over the history.
    Hint 3: mgr = DiagnosticManager(fail_threshold=fail_n, heal_threshold=heal_n);  for failed in history: mgr.report("P0100", failed)
            then compare   mgr.active_codes() == ["P0100"]   with your model's `active` (and `stored_codes()` with `stored`).
            Careful: with an EMPTY history the code was never reported, so both lists are empty.
    """
    todo("write the model and the property")


def test_custom_strategy():
    """Exercise 3 - build your own strategy for valid CAN frames and use it.
    Hint 1: frames = st.builds(CANFrame, arbitration_id=st.integers(0, 0x7FF), data=st.binary(max_size=8))
    Hint 2: property: for every frame, e2e_check(e2e_protect(frame.data[:6], 3), 3) returns E2EStatus.OK and the same payload.
    """
    todo("write the strategy and the property")
