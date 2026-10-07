"""Solutions - Lab 4 (test doubles)."""
from unittest import mock

import pytest

from autotest.ecu import InstrumentCluster, WheelSpeedECU
from autotest.sensors import TemperatureSensor


class SpyListener:
    def __init__(self):
        self.frames = []

    def __call__(self, frame):
        self.frames.append(frame)


def test_alive_counter_increments(bus):
    spy = SpyListener()
    bus.subscribe(spy)
    ecu = WheelSpeedECU(bus)
    for speed in (10, 20, 30):
        ecu.send_speed(speed)
    assert [f.data[1] for f in spy.frames] == [0, 1, 2]


def test_adc_hardware_error_propagates():
    adc = mock.Mock()
    adc.read.side_effect = OSError("bus error")
    with pytest.raises(OSError):                 # documented behaviour: not swallowed, not converted
        TemperatureSensor(adc).read()
    adc.read.assert_called_once_with()


@pytest.mark.parametrize("age, shown", [(0.09, "60"), (0.099, "60"), (0.101, "--"), (0.11, "--")])
def test_cluster_timeout_boundary(bus, clock, age, shown):
    cluster = InstrumentCluster(bus, clock)
    WheelSpeedECU(bus).send_speed(60)
    clock.advance(age)                           # time.sleep(0.11) would slow the suite AND be flaky
    assert cluster.displayed_speed() == shown


# 4 - A mock-based test is BAD when it (a) re-states the implementation line by line, so every
# refactoring breaks it, (b) mocks something cheap and pure (use the real object), or
# (c) never checks an observable outcome - it only proves the mock was configured.
