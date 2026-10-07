"""Lab 8 - robustness: negative tests, fault injection and fuzzing.

Question changes from "does it work?" to "does it fail SAFELY?".
"""
import math
import random

import pytest
from hypothesis import given, settings, strategies as st

from autotest.bms import BatteryManagementSystem, BMSFault, max_charge_current
from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.diagnostics import DiagnosticManager
from autotest.ecu import InstrumentCluster, WheelSpeedECU
from autotest.sensors import SensorFault, TemperatureSensor

pytestmark = pytest.mark.robustness


# ---- 1. sensor fault injection: wrap a healthy source and corrupt it --------------------
class FaultyADC:
    """Decorator around any ADC that injects classic automotive sensor faults."""

    def __init__(self, inner, mode, after=0):
        self.inner, self.mode, self.after, self.n, self.last = inner, mode, after, 0, None

    def read(self):
        value = self.inner.read()
        self.n += 1
        if self.n <= self.after:
            self.last = value
            return value
        if self.mode == "stuck":          # stuck-at last good value
            return self.last
        if self.mode == "short_gnd":
            return 0
        if self.mode == "open":
            return 4095
        raise AssertionError(self.mode)


class ConstADC:
    def __init__(self, v):
        self.v = v

    def read(self):
        return self.v


@pytest.mark.parametrize("mode, message", [("short_gnd", "ground"), ("open", "open circuit")])
def test_hard_faults_are_reported_not_converted_to_a_temperature(mode, message):
    sensor = TemperatureSensor(FaultyADC(ConstADC(2000), mode, after=2))
    sensor.read(), sensor.read()
    with pytest.raises(SensorFault, match=message):
        sensor.read()


def test_stuck_sensor_is_NOT_detected_today_documenting_a_gap():
    sensor = TemperatureSensor(FaultyADC(ConstADC(2000), "stuck", after=1))
    values = {sensor.read() for _ in range(50)}
    assert len(values) == 1   # a stuck value looks perfectly healthy -> a plausibility check is missing


# ---- 2. bus fault injection with a seeded RNG (reproducible!) ----------------------------
@pytest.mark.parametrize("seed", range(5))
def test_cluster_never_displays_an_invented_speed_under_bit_errors(seed, clock):
    rng = random.Random(seed)
    bus = VirtualCANBus()
    ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)

    def flip_a_bit_sometimes(frame):
        if rng.random() < 0.3:
            data = bytearray(frame.data)
            data[rng.randrange(len(data))] ^= 1 << rng.randrange(8)
            return CANFrame(frame.arbitration_id, bytes(data))
        return frame

    bus.add_fault(flip_a_bit_sometimes)
    sent = set()
    for i in range(200):
        speed = float(rng.randrange(0, 250))
        sent.add(f"{speed:.0f}")
        ecu.send_speed(speed)
        clock.advance(0.01)
        shown = cluster.displayed_speed()
        assert shown == "--" or shown in sent, f"frame {i}: displayed invented value {shown}"


def test_duplicate_frames_are_rejected_by_alive_counter(clock):
    bus = VirtualCANBus()
    cluster = InstrumentCluster(bus, clock)
    ecu = WheelSpeedECU(bus)
    ecu.send_speed(50)
    duplicate = bus.log[-1]
    bus.send(duplicate)                      # replayed frame, same counter
    assert cluster.diag._dtcs["U0100"].fail_count == 1


# ---- 3. fuzzing the diagnostic interface: random bytes in, SANE bytes out ----------------
@settings(max_examples=500, deadline=None)
@given(st.binary(max_size=20))
@pytest.mark.requirement("REQ-DIAG-002")
def test_uds_handler_never_raises_and_always_answers_with_a_valid_response(request_bytes):
    response = DiagnosticManager().handle_request(request_bytes)
    assert isinstance(response, bytes) and response
    assert response[0] in (0x7F, 0x59, 0x54, 0x62)
    if response[0] == 0x7F:
        assert len(response) == 3


@pytest.mark.requirement("REQ-DIAG-002")
@given(st.integers(0, 255).filter(lambda s: s not in (0x14, 0x19, 0x22)), st.binary(max_size=6))
def test_unknown_service_gets_negative_response_0x11(service, rest):
    assert DiagnosticManager().handle_request(bytes([service]) + rest) == bytes([0x7F, service, 0x11])


def test_seeded_random_fuzz_is_reproducible_in_ci():
    """Plain-pytest fuzzing: seed printed on failure -> anyone can replay it."""
    rng = random.Random(1234)
    mgr = DiagnosticManager()
    for _ in range(2000):
        blob = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 12)))
        mgr.handle_request(blob)


# ---- 4. hostile numeric input: NaN / inf -----------------------------------------------
@pytest.mark.parametrize("bad", [math.inf, -math.inf])
def test_infinite_temperature_is_handled_safely(bad):
    assert max_charge_current(50, bad) == 0.0


@pytest.mark.xfail(strict=True, reason="BUG-201: NaN temperature falls through every comparison -> FULL charge current")
def test_nan_temperature_must_not_allow_charging():
    try:
        current = max_charge_current(50, math.nan)
    except ValueError:      # rejecting the input is as safe as returning 0 A
        return
    assert current == 0.0


@pytest.mark.xfail(strict=True, reason="BUG-202: NaN cell voltage is never > max or < min -> reported healthy")
def test_nan_cell_voltage_must_raise_a_fault_or_error():
    try:
        fault = BatteryManagementSystem().evaluate([3.7, math.nan, 3.7], 25)
    except ValueError:
        return
    assert fault is not BMSFault.NONE


# ---- 5. recovery: the system must come back after the fault is gone -----------------------
def test_dtc_heals_after_enough_good_cycles():
    d = DiagnosticManager(fail_threshold=2, heal_threshold=3)
    for _ in range(2):
        d.report("U0121", failed=True)
    assert d.active_codes() == ["U0121"]
    for _ in range(3):
        d.report("U0121", failed=False)
    assert d.active_codes() == [] and d.stored_codes() == ["U0121"]   # history is kept
