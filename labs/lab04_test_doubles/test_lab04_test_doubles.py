"""Lab 4 - test doubles: dummy, stub, fake, spy and mock.

The SUT depends on hardware (an ADC) and on a diagnostic manager. We replace those
collaborators so the test is fast, deterministic, and can force rare situations.
"""
from unittest import mock

import pytest

from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.diagnostics import DiagnosticManager
from autotest.ecu import DTC_COMM_LOST, InstrumentCluster, WheelSpeedECU
from autotest.sensors import SensorFault, TemperatureSensor


# ---- STUB: returns canned answers ------------------------------------------------
class StubADC:
    def __init__(self, counts):
        self.counts = counts

    def read(self):
        return self.counts


def test_stub_forces_a_wiring_fault_that_real_hardware_rarely_produces():
    with pytest.raises(SensorFault, match="short to ground"):
        TemperatureSensor(StubADC(0)).read()


# ---- FAKE: a working but simplified implementation -------------------------------
class SineWaveADC:
    """Plays back a sequence like a data logger would."""

    def __init__(self, samples):
        self._it = iter(samples)

    def read(self):
        return next(self._it)


def test_fake_playback_feeds_the_moving_average():
    sensor = TemperatureSensor(SineWaveADC([1000, 2000, 3000, 2000]), filter_len=2)
    readings = [sensor.read_filtered() for _ in range(4)]
    expected_second = (TemperatureSensor.T_MIN + 190 * 1000 / 4095 + TemperatureSensor.T_MIN + 190 * 2000 / 4095) / 2
    assert readings[1] == pytest.approx(expected_second)
    assert readings[0] < readings[2]  # trend follows the input


# ---- SPY: real object that records how it was used -------------------------------
class SpyADC:
    def __init__(self, counts):
        self.counts, self.calls = counts, 0

    def read(self):
        self.calls += 1
        return self.counts


def test_spy_counts_hardware_accesses():
    spy = SpyADC(2000)
    sensor = TemperatureSensor(spy, filter_len=3)
    for _ in range(3):
        sensor.read_filtered()
    assert spy.calls == 3  # exactly one ADC conversion per call: no hidden re-reads


# ---- MOCK (unittest.mock): verify INTERACTIONS ------------------------------------
def test_mock_verifies_the_cluster_reports_to_diagnostics(clock):
    bus = VirtualCANBus()
    diag = mock.Mock(spec=DiagnosticManager)  # spec= makes typos in method names fail
    cluster = InstrumentCluster(bus, clock, diag)

    clock.advance(0.5)                         # no frames for 500 ms
    assert cluster.displayed_speed() == "--"

    diag.report.assert_called_with(DTC_COMM_LOST, failed=True)


def test_mock_side_effect_simulates_intermittent_failure():
    adc = mock.Mock()
    adc.read.side_effect = [2048, 2048, 0, 2048]    # third read: fault
    sensor = TemperatureSensor(adc)
    assert sensor.read() == pytest.approx(55.0, abs=0.05)
    sensor.read()
    with pytest.raises(SensorFault):
        sensor.read()
    assert adc.read.call_count == 3


# ---- patching: replace a name where it is LOOKED UP --------------------------------
def test_patch_replaces_collaborator_for_the_duration_of_the_test():
    with mock.patch("autotest.ecu.e2e_protect", return_value=b"\x00\x00\x00\x00\x00") as fake:
        bus = VirtualCANBus()
        WheelSpeedECU(bus).send_speed(50)
    fake.assert_called_once()
    assert bus.log[0].data == b"\x00\x00\x00\x00\x00"


def test_monkeypatch_equivalent_in_pytest(monkeypatch):
    monkeypatch.setattr("autotest.ecu.e2e_protect", lambda payload, counter: b"\xAA" + payload)
    bus = VirtualCANBus()
    WheelSpeedECU(bus).send_speed(10)
    assert bus.log[0].data[0] == 0xAA


# ---- DUMMY: fills a parameter that is never used ------------------------------------
def test_dummy_listener_is_never_called_for_other_ids():
    bus = VirtualCANBus()
    listener = mock.Mock()
    bus.subscribe(listener, ids={0x100})
    bus.send(CANFrame(0x200, b"\x01"))
    listener.assert_not_called()


# ---- Anti-pattern warning ------------------------------------------------------------
def test_do_not_over_mock_real_collaborator_is_cheaper_here(clock):
    """The real DiagnosticManager is pure and fast, so using it beats a mock:
    we assert on OUTCOMES (state), not on call choreography."""
    diag = DiagnosticManager(fail_threshold=2)
    cluster = InstrumentCluster(VirtualCANBus(), clock, diag)
    clock.advance(1)
    cluster.displayed_speed()
    cluster.displayed_speed()
    assert diag.active_codes() == [DTC_COMM_LOST]
