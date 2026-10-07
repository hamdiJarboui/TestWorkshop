"""Lab 0 exercises - your very first tests.

  Run it:       python course.py exercise 0
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the
                test; the test then passes only if what you wrote is correct.
  Done when:    `python course.py progress` shows every test of Lab 0 passing.
"""
import pytest

from autotest.learn import todo
from autotest.sensors import kmh_to_ms, wheel_speed_kmh


def test_72_kmh_is_20_metres_per_second():
    """Goal: check that kmh_to_ms(72) is 20 m/s.

    Hint 1: call the function and keep the result:   result = kmh_to_ms(72)
    Hint 2: compare it:   assert result == pytest.approx(20.0)
    """
    todo("call kmh_to_ms(72) and assert the result is 20")


def test_an_interval_of_zero_seconds_is_rejected():
    """Goal: wheel_speed_kmh must refuse an interval of 0 seconds (you cannot divide by zero time).

    Hint 1: a function that must raise an error is tested with a `with pytest.raises(...)` block.
    Hint 2: the error type is ValueError.
    Hint 3: with pytest.raises(ValueError):
                wheel_speed_kmh(pulses=10, pulses_per_rev=20, circumference_m=2.0, interval_s=0)
    """
    todo("assert that interval_s=0 raises ValueError")
