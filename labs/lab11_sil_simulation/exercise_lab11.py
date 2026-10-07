"""Lab 11 exercises - closed-loop (SIL) acceptance tests.

  Run it:       python course.py exercise 11
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the test.
  Done when:    `python course.py progress` shows every test of Lab 11 passing.
"""
import pytest

import autotest.abs as abs_module
from autotest.abs import simulate_braking
from autotest.cruise import CruiseController
from autotest.learn import todo
from autotest.vehicle import Vehicle, run_cruise


def hill_metrics(kp, ki, grade):
    """Helper (given): a hill of `grade` (0.08 = 8 %) starts at t = 20 s. Returns (dip_kmh, recovery_s)."""
    cc = CruiseController(kp, ki)
    cc.power_on()
    cc.set(100)
    trace = run_cruise(cc, 100, 120, grade_profile=lambda t: grade if t >= 20 else 0.0)
    dip = 100 - min(v for t, v, _ in trace if t >= 20)
    recovery = max(t for t, v, _ in trace if abs(v - 100) > 1) - 20
    return dip, recovery


def test_8_percent_hill_meets_the_acceptance_criteria():
    """Exercise 1 - requirement: on an 8 % hill the speed dips by at most 4 km/h and is back within 1 km/h in 20 s.
    Does the DEFAULT controller (kp=0.05, ki=0.01) pass? Find out FIRST, then tune.

    Hint 1: print(hill_metrics(0.05, 0.01, 0.08)) in a Python shell, or temporarily in the test.
    Hint 2: try larger gains, e.g. (0.1, 0.02), (0.15, 0.02), (0.2, 0.03) - write the sweep as a parametrized test.
    Hint 3: dip, recovery = hill_metrics(kp, ki, 0.08);  assert dip <= 4.0 and recovery <= 20.0
    Finally: state your chosen gains in a comment and one downside of raising them (hint: noise).
    """
    todo("write the sweep and the criteria")


def test_abs_still_helps_on_ice(monkeypatch):
    """Exercise 2 - low-friction surface: scale the tyre friction curve to 0.3 of normal. ABS must still beat locked-wheel braking.

    Hint 1: original = abs_module.tyre_mu
    Hint 2: monkeypatch.setattr(abs_module, "tyre_mu", lambda slip: 0.3 * original(slip))
    Hint 3: compare simulate_braking(True)["distance_m"] with simulate_braking(False)["distance_m"]; is the 10 % improvement criterion still met?
    """
    todo("monkeypatch the friction curve and compare")


def test_biased_speed_sensor_shifts_the_real_speed():
    """Exercise 3 - the controller's speed input reads 5 km/h TOO LOW. Predict the real steady-state speed, then measure it.

    Hint 1: car = Vehicle(speed_ms=100 / 3.6);  loop 3000 times:  throttle = cc.control(car.speed_kmh - 5.0, 0.1);  car.step(throttle, 0.1)
    Hint 2: the controller believes it is at target when the SENSOR says 100, so the real speed settles at ... ?
    Then, in a comment: which diagnostic or plausibility check would catch this in the field?
    """
    todo("simulate the biased sensor and assert the real speed")
