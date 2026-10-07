"""Solutions - Lab 11 (SIL)."""
import pytest

import autotest.abs as abs_module
from autotest.abs import simulate_braking
from autotest.cruise import CruiseController
from autotest.vehicle import Vehicle, run_cruise

pytestmark = pytest.mark.sil


def hill_metrics(kp, ki, grade=0.08):
    cc = CruiseController(kp, ki)
    cc.power_on()
    cc.set(100)
    trace = run_cruise(cc, 100, 120, grade_profile=lambda t: grade if t >= 20 else 0.0)
    dip = 100 - min(v for t, v, _ in trace if t >= 20)
    recovery = max(t for t, v, _ in trace if abs(v - 100) > 1) - 20
    return dip, recovery


def test_default_gains_do_NOT_meet_the_8_percent_hill_criteria():
    dip, _ = hill_metrics(0.05, 0.01)
    assert dip > 4.0                                  # 5.4 km/h: the requirement exposes weak tuning


@pytest.mark.parametrize("kp, ki", [(0.1, 0.02), (0.15, 0.02), (0.2, 0.03)])
def test_retuned_gains_meet_the_8_percent_hill_criteria(kp, ki):
    dip, recovery = hill_metrics(kp, ki)
    assert dip <= 4.0 and recovery <= 20.0
    # chosen: kp=0.15, ki=0.02 - smallest gains with healthy margin on BOTH criteria (see COURSE_DESIGN.md)


def test_ice(monkeypatch):
    original = abs_module.tyre_mu
    monkeypatch.setattr(abs_module, "tyre_mu", lambda s: 0.3 * original(s))
    with_abs, without = simulate_braking(True), simulate_braking(False)
    assert with_abs["distance_m"] < without["distance_m"]
    assert with_abs["distance_m"] < 0.9 * without["distance_m"]     # the 10 % criterion still holds


def test_biased_speed_sensor_shifts_the_real_speed_by_the_bias():
    cc = CruiseController()
    cc.power_on()
    cc.set(100)
    car, bias = Vehicle(speed_ms=100 / 3.6), -5.0
    for _ in range(3000):
        car.step(cc.control(car.speed_kmh + bias, 0.1), 0.1)
    # The controller thinks it is at 100 km/h while the car is at 105. Integral action cannot see
    # the error: needs a plausibility cross-check (wheel speed vs GPS/ABS) + a DTC for sensor drift.
    assert car.speed_kmh == pytest.approx(105.0, abs=0.2)
