"""Lab 0 - three tiny tests. Run:  python course.py lab 0

A test is just a function whose name starts with `test_`; `assert` is the check.
"""
import pytest

from autotest.sensors import kmh_to_ms, ms_to_kmh, wheel_speed_kmh


@pytest.mark.smoke
def test_36_kmh_is_10_metres_per_second():
    # Arrange + Act: call the code under test
    result = kmh_to_ms(36)
    # Assert: compare with the value from the SPECIFICATION (36 km/h = 10 m/s), not from the code
    assert result == pytest.approx(10.0)


def test_converting_there_and_back_gives_the_same_speed():
    assert ms_to_kmh(kmh_to_ms(50)) == pytest.approx(50)


def test_a_wheel_speed_of_zero_pulses_is_standstill():
    # 0 pulses in 1 second -> the wheel is not turning
    assert wheel_speed_kmh(pulses=0, pulses_per_rev=20, circumference_m=2.0, interval_s=1.0) == 0
