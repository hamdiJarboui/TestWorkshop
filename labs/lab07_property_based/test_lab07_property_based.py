"""Lab 7 - property-based testing with Hypothesis.

Instead of hand-picking inputs, state a PROPERTY that must hold for ALL inputs and let
Hypothesis search (and shrink) counter-examples.
"""
import pytest
from hypothesis import assume, example, given, settings, strategies as st

from autotest.bms import max_charge_current
from autotest.can import CANFrame, CANMessage, E2EStatus, Signal, crc8, e2e_check, e2e_protect
from autotest.sensors import kmh_to_ms, ms_to_kmh

payloads = st.binary(min_size=0, max_size=6)


# ---- property 1: round trip (encode then decode == identity) ---------------------------
@pytest.mark.requirement("REQ-CAN-002")
@given(st.floats(min_value=0, max_value=300, allow_nan=False))
def test_wheel_speed_round_trip_within_one_resolution_step(speed):
    sig = Signal("speed", 0, 16, factor=0.01, minimum=0, maximum=300)
    assert sig.to_physical(sig.to_raw(speed)) == pytest.approx(speed, abs=0.005 + 1e-9)


@given(st.integers(0, 65535), st.integers(-40, 215))
def test_message_round_trip_for_any_raw_values(rpm_raw, temp_raw):
    msg = CANMessage(1, "m", 4, (Signal("rpm", 0, 16, 0.25), Signal("t", 16, 8, offset=-40)))
    values = {"rpm": rpm_raw * 0.25, "t": float(temp_raw)}
    assert msg.decode(msg.encode(values)) == pytest.approx(values)


@given(st.floats(min_value=-1e4, max_value=1e4))
def test_unit_conversion_round_trip(kmh):
    assert ms_to_kmh(kmh_to_ms(kmh)) == pytest.approx(kmh)


# ---- property 2: end-to-end protection detects every corruption we can generate -----------
@pytest.mark.requirement("REQ-CAN-003")
@given(payloads, st.integers(0, 15))
def test_e2e_accepts_what_it_protects(payload, counter):
    status, out = e2e_check(e2e_protect(payload, counter), counter)
    assert status is E2EStatus.OK and out == payload


@pytest.mark.requirement("REQ-CAN-003")
@given(payloads, st.integers(0, 15), st.data())
def test_e2e_detects_any_single_bit_flip(payload, counter, data):
    protected = bytearray(e2e_protect(payload, counter))
    bit = data.draw(st.integers(0, len(protected) * 8 - 1))
    protected[bit // 8] ^= 1 << (bit % 8)
    status, _ = e2e_check(bytes(protected))
    assert status is not E2EStatus.OK


@given(st.binary(max_size=8))
def test_crc_is_always_one_byte_and_deterministic(data):
    assert 0 <= crc8(data) <= 255 and crc8(data) == crc8(data)


# ---- property 3: safety invariants of the BMS -------------------------------------------
@pytest.mark.requirement("REQ-BMS-001")
@given(st.floats(0, 100), st.floats(-60, 120))
def test_charge_current_is_always_within_physical_limits(soc, temp):
    i = max_charge_current(soc, temp)
    assert 0.0 <= i <= 100.0
    if temp < 0 or temp > 45:
        assert i == 0.0  # safety property: never charge outside the temperature window


@given(st.floats(0, 100), st.floats(0, 100), st.floats(10, 45))
def test_charge_current_never_increases_with_soc(a, b, temp):
    low, high = sorted((a, b))
    assert max_charge_current(high, temp) <= max_charge_current(low, temp) + 1e-9


# ---- property 4: validation never crashes in unexpected ways ----------------------------
@given(st.integers(-10_000, 0x30000000), st.booleans(), st.binary(max_size=12))
def test_canframe_either_builds_or_raises_valueerror(arb_id, ext, data):
    try:
        frame = CANFrame(arb_id, data, ext)
    except ValueError:
        return
    assert frame.dlc == len(data) <= 8 and 0 <= frame.arbitration_id <= (0x1FFFFFFF if ext else 0x7FF)


# ---- steering Hypothesis: @example, settings, assume() (and why NOT to over-filter) --------
# Anti-pattern: `assume(abs(a - b) < 0.01)` on two independent floats rejects ~100 % of inputs
# and Hypothesis aborts with FailedHealthCheck(filter_too_much). Generate the SMALL DELTA directly.
@settings(max_examples=200, deadline=None)
@given(st.floats(0, 99.99), st.floats(0, 0.01))
@example(80.0, 0.0)           # always re-test this edge case, in addition to random ones
def test_taper_is_continuous_at_80_percent(soc, delta):
    assume(soc + delta <= 100)   # cheap, rarely-triggered filter: fine
    assert abs(max_charge_current(soc, 25) - max_charge_current(soc + delta, 25)) < 1.0


# ---- the point of shrinking: a deliberately wrong property, kept as a documented xfail -----
@pytest.mark.xfail(strict=True, reason="demo: Hypothesis shrinks to the smallest counter-example")
@given(st.floats(min_value=0, max_value=300))
def test_wrong_property_resolution_is_exact(speed):
    sig = Signal("speed", 0, 16, factor=0.01)
    assert sig.to_physical(sig.to_raw(speed)) == speed   # false: quantisation error
