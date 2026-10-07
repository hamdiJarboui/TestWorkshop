"""Solutions - Lab 7 (property-based)."""
from hypothesis import given, strategies as st

from autotest.abs import slip_ratio
from autotest.can import CANFrame, E2EStatus, e2e_check, e2e_protect
from autotest.diagnostics import DiagnosticManager

speeds = st.floats(min_value=0, max_value=100, allow_nan=False)


@given(speeds, speeds)
def test_slip_is_always_between_0_and_1(vehicle, wheel):
    assert 0.0 <= slip_ratio(vehicle, wheel) <= 1.0


@given(st.floats(min_value=0.6, max_value=100))
def test_free_rolling_has_no_slip(v):
    assert slip_ratio(v, v) == 0.0


@given(st.floats(min_value=0.6, max_value=100))
def test_locked_wheel_is_full_slip(v):
    assert slip_ratio(v, 0.0) == 1.0


@given(st.lists(st.booleans(), max_size=40), st.integers(1, 4), st.integers(1, 4))
def test_dtc_matches_reference_model(history, fail_n, heal_n):
    # independent re-implementation of the SPEC (not of the code): keeps two streak counters
    fails = passes = 0
    active = stored = False
    for failed in history:
        if failed:
            fails, passes = fails + 1, 0
            if fails >= fail_n:
                active = stored = True
        else:
            passes, fails = passes + 1, 0
            if passes >= heal_n:
                active = False
    mgr = DiagnosticManager(fail_threshold=fail_n, heal_threshold=heal_n)
    for failed in history:
        mgr.report("P0100", failed)
    assert (mgr.active_codes() == ["P0100"]) == (active and bool(history))
    assert (mgr.stored_codes() == ["P0100"]) == (stored and bool(history))


frames = st.builds(CANFrame, arbitration_id=st.integers(0, 0x7FF), data=st.binary(max_size=8))


@given(frames)
def test_custom_strategy(frame):
    status, payload = e2e_check(e2e_protect(frame.data[:6], 3), 3)
    assert status is E2EStatus.OK and payload == frame.data[:6]
