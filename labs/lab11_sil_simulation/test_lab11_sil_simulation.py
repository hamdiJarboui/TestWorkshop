"""Lab 11 - software-in-the-loop (SIL): the controller runs against a simulated plant.

Open-loop unit tests say "the function returns 0.7". Closed-loop tests say "the CAR reaches
100 km/h without overshooting more than 4 km/h". Acceptance criteria are written as measurable numbers.
"""
import pytest

from autotest.abs import ABSController, Valve, simulate_braking, tyre_mu
from autotest.cruise import CruiseController, CruiseState
from autotest.vehicle import Vehicle, run_cruise

pytestmark = [pytest.mark.sil, pytest.mark.system]


# ---------------------------------------------------------------- helpers: metrics -------------
def settling_time(trace, target, band=1.0):
    """First time after which speed stays within +/- band of the target."""
    last_bad = max((t for t, v, _ in trace if abs(v - target) > band), default=-1.0)
    return last_bad + (trace[1][0] - trace[0][0])


def overshoot_pct(trace, target, start):
    return max(0.0, (max(v for _, v, _ in trace) - target) / (target - start) * 100)


@pytest.fixture
def cruise_at_100():
    cc = CruiseController()
    cc.power_on()
    cc.set(100)
    return cc


# ---------------------------------------------------------------- plant sanity (test the model!) ----
def test_plant_coasts_down_without_throttle():
    car = Vehicle(speed_ms=30)
    for _ in range(600):
        car.step(0.0, 0.1)
    assert 0 < car.speed_ms < 30


def test_plant_cannot_exceed_physical_top_speed():
    car = Vehicle()
    for _ in range(20000):
        car.step(1.0, 0.1)
    assert 200 < car.speed_kmh < 300   # drag balance


def test_plant_steep_grade_slows_the_car():
    flat, hill = Vehicle(speed_ms=25), Vehicle(speed_ms=25)
    for _ in range(100):
        flat.step(0.2, 0.1, 0.0)
        hill.step(0.2, 0.1, 0.08)
    assert hill.speed_ms < flat.speed_ms


# ---------------------------------------------------------------- cruise acceptance ---------------
def test_reaches_target_from_80_with_acceptable_dynamics(cruise_at_100):
    trace = run_cruise(cruise_at_100, start_kmh=80, duration_s=120)
    assert overshoot_pct(trace, 100, 80) < 20.0        # i.e. below 4 km/h on a 20 km/h step
    assert settling_time(trace, 100, band=1.0) < 25.0
    assert abs(trace[-1][1] - 100) < 0.1               # zero steady-state error (integral action)


def test_holds_speed_when_a_5_percent_hill_starts(cruise_at_100):
    trace = run_cruise(cruise_at_100, 100, 120, grade_profile=lambda t: 0.05 if t >= 20 else 0.0)
    assert min(v for t, v, _ in trace if t >= 20) > 96.0       # dip no larger than 4 km/h
    assert abs(trace[-1][1] - 100) < 0.5                       # and fully recovered


def test_throttle_never_leaves_0_1_even_for_huge_errors():
    cc = CruiseController()
    cc.power_on()
    cc.set(180)
    trace = run_cruise(cc, 30, 60)
    assert all(0.0 <= u <= 1.0 for _, _, u in trace)


@pytest.mark.requirement("REQ-CC-002")
def test_brake_event_in_the_loop_hands_back_control(cruise_at_100):
    brake_at_30s = {30.0: lambda cc, car: cc.brake()}
    trace = run_cruise(cruise_at_100, 100, 40, events=brake_at_30s)
    assert cruise_at_100.state is CruiseState.STANDBY
    assert all(u == 0.0 for t, _, u in trace if t > 30)


def test_resume_brings_the_car_back_to_the_saved_speed(cruise_at_100):
    ev = {20.0: lambda cc, car: cc.cancel(), 40.0: lambda cc, car: cc.resume(car.speed_kmh)}
    trace = run_cruise(cruise_at_100, 100, 120, events=ev)
    mid = next(v for t, v, _ in trace if t == 39.0)
    assert mid < 100                         # slowed down while cancelled
    assert abs(trace[-1][1] - 100) < 0.5     # and came back


@pytest.mark.parametrize("target", [40, 70, 100, 130, 160])
def test_converges_for_every_target_in_the_envelope(target):
    cc = CruiseController()
    cc.power_on()
    cc.set(target)
    trace = run_cruise(cc, target - 10, 200)
    assert abs(trace[-1][1] - target) < 0.5


# ---------------------------------------------------------------- ABS acceptance -------------------
def test_tyre_model_peaks_at_20_percent_slip():
    assert max(tyre_mu(s / 100) for s in range(101)) == pytest.approx(1.0)
    assert tyre_mu(0.2) > tyre_mu(1.0)


@pytest.mark.parametrize("vehicle, wheel, expected", [
    (30, 30, Valve.APPLY),        # rolling freely
    (30, 21, Valve.HOLD),         # 30 % slip? -> see below
    (30, 20, Valve.RELEASE),
    (3, 0, Valve.APPLY),          # below 5 m/s ABS stays out of the way
])
def test_abs_decisions(vehicle, wheel, expected):
    actual = ABSController().decide(vehicle, wheel)
    if (vehicle, wheel) == (30, 21):                # 30 % slip is above the 25 % release limit
        expected = Valve.RELEASE
    assert actual is expected


@pytest.mark.requirement("REQ-ABS-001")
def test_wheel_does_not_lock_while_abs_is_active():
    result = simulate_braking(use_abs=True)
    assert result["locked_s"] == 0.0
    assert result["peak_slip"] < 0.35


@pytest.mark.requirement("REQ-ABS-002")
def test_abs_shortens_stopping_distance_by_at_least_10_percent():
    with_abs, without = simulate_braking(True), simulate_braking(False)
    assert with_abs["distance_m"] < 0.9 * without["distance_m"]


def test_baseline_without_abs_locks_the_wheel():
    """The 'control group': proves the scenario really is dangerous, so the ABS test means something."""
    assert simulate_braking(use_abs=False)["locked_s"] > 1.0


def test_simulation_is_deterministic():
    assert simulate_braking(True) == simulate_braking(True)
