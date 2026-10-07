"""Lab 4 exercises - test doubles: spy, mock, fake clock.

  Run it:       python course.py exercise 4
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the
                test; the test then passes only if what you wrote is correct.
  Done when:    `python course.py progress` shows every test of Lab 4 passing.
"""
from unittest import mock

import pytest

from autotest.ecu import InstrumentCluster, WheelSpeedECU
from autotest.learn import todo
from autotest.sensors import TemperatureSensor

# The fixtures `bus` (a VirtualCANBus) and `clock` (a FakeClock) come from the course's conftest.py:
# just list them as test arguments.


class SpyListener:
    """A SPY records what happened to it. Complete it: a callable that stores every frame it receives."""

    def __init__(self):
        self.frames = []

    def __call__(self, frame):
        todo("store the frame:  self.frames.append(frame)")


def test_alive_counter_increments(bus):
    """Exercise 1 (SPY). Subscribe a SpyListener to the bus, let a WheelSpeedECU send 3 frames, and check that the
    alive counter (byte 1 of each frame's data) goes 0, 1, 2.

    Hint 1: spy = SpyListener();  bus.subscribe(spy);  ecu = WheelSpeedECU(bus);  ecu.send_speed(10) ... (three times)
    Hint 2: assert [f.data[1] for f in spy.frames] == [0, 1, 2]
    """
    todo("spy on the bus and check the counters")


def test_adc_hardware_error_propagates():
    """Exercise 2 (MOCK with a side effect). A real ADC can raise OSError. What does TemperatureSensor do with it?
    Document the behaviour with a test.

    Hint 1: adc = mock.Mock();  adc.read.side_effect = OSError("bus error")
    Hint 2: build the sensor with the mock and call read() inside  with pytest.raises(OSError):
    Hint 3: adc.read.assert_called_once_with()   # verify the interaction too
    """
    todo("mock an ADC that raises OSError")


@pytest.mark.parametrize("age, shown", [
    (0.09, "60"),
    # TODO: add rows for the boundary: just inside the 100 ms timeout (0.099) and just outside (0.101), and 0.11
])
def test_cluster_timeout_boundary(bus, clock, age, shown):
    """Exercise 3 (FAKE clock). Send speed 60, advance the fake clock by `age` seconds, ask the cluster what it shows.

    Hint 1: cluster = InstrumentCluster(bus, clock);  WheelSpeedECU(bus).send_speed(60)
    Hint 2: clock.advance(age);  assert cluster.displayed_speed() == shown
    Think: why is time.sleep(0.11) the WRONG tool here? (Two reasons - write them as a comment.)
    """
    todo("complete the table and the test body")


# Exercise 4 - reflection (no code): in a comment, write 3 sentences on WHEN a mock-based test is a BAD test.
