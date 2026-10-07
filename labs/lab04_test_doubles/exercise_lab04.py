"""Lab 4 exercises. Run: pytest labs/lab04_test_doubles/exercise_lab04.py -v"""
import pytest
from unittest import mock

from autotest.bus import VirtualCANBus
from autotest.ecu import InstrumentCluster, WheelSpeedECU
from autotest.sensors import TemperatureSensor


# Exercise 1 - SPY: write SpyListener (records frames). Send 3 speeds from WheelSpeedECU and
# assert the alive counter in data[1] goes 0, 1, 2.
def test_alive_counter_increments():
    pytest.fail("TODO")


# Exercise 2 - MOCK: use mock.Mock(spec=...) for an ADC whose read() raises OSError once.
# What does TemperatureSensor do? Document the behaviour with pytest.raises.
def test_adc_hardware_error_propagates():
    pytest.fail("TODO")


# Exercise 3 - FAKE: write FakeClock-driven test: speed frame at t=0, ask at t=0.09 s (shows number)
# and at t=0.11 s (shows "--"). Why is time.sleep() the wrong tool here?
def test_cluster_timeout_boundary(clock):
    pytest.fail("TODO")


# Exercise 4 - Reflection (write 3 sentences in a comment): when is a mock-based test BAD?
