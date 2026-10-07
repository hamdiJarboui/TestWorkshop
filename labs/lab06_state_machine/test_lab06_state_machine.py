"""Lab 6 - state-transition and system-level testing of the cruise controller.

Technique: draw the state machine, then cover (a) every state, (b) every VALID transition,
(c) every INVALID event in every state ("0-switch" and invalid-transition coverage).

      power_on          set(v)              brake/cancel
  OFF ---------> STANDBY ----------> ACTIVE ------------> STANDBY
   ^   <--- power_off (any state) ---    |  ^
                                accel    v  | release
                                      OVERRIDE
"""
import itertools

import pytest

from autotest.cruise import CruiseController, CruiseState as S

pytestmark = pytest.mark.system


@pytest.fixture
def cc():
    return CruiseController()


@pytest.fixture
def active(cc):
    cc.power_on()
    assert cc.set(100)
    return cc


# ---- valid transitions -------------------------------------------------------------
def test_initial_state_is_off(cc):
    assert cc.state is S.OFF and cc.target is None


def test_off_to_standby(cc):
    cc.power_on()
    assert cc.state is S.STANDBY


@pytest.mark.requirement("REQ-CC-001")
def test_standby_to_active_with_set(cc):
    cc.power_on()
    assert cc.set(100) is True
    assert (cc.state, cc.target) == (S.ACTIVE, 100)


@pytest.mark.requirement("REQ-CC-002")
def test_brake_cancels_and_remembers_target(active):
    active.brake()
    assert active.state is S.STANDBY and active.target is None
    assert active.saved_target == 100


def test_resume_restores_saved_target(active):
    active.cancel()
    assert active.resume(current_speed_kmh=90) is True
    assert (active.state, active.target) == (S.ACTIVE, 100)


def test_accelerator_overrides_then_returns_to_active(active):
    active.accelerator(True)
    assert active.state is S.OVERRIDE
    active.accelerator(False)
    assert active.state is S.ACTIVE


def test_set_while_active_changes_target(active):
    assert active.set(120)
    assert active.target == 120


@pytest.mark.parametrize("state_setup", ["off", "standby", "active", "override"])
def test_power_off_from_every_state_clears_everything(cc, state_setup):
    if state_setup != "off":
        cc.power_on()
    if state_setup in ("active", "override"):
        cc.set(100)
    if state_setup == "override":
        cc.accelerator(True)
    cc.power_off()
    assert (cc.state, cc.target, cc.saved_target) == (S.OFF, None, None)


# ---- invalid events (negative transitions) ------------------------------------------
def test_set_is_refused_when_off(cc):
    assert cc.set(100) is False and cc.state is S.OFF


@pytest.mark.requirement("REQ-CC-001")
@pytest.mark.parametrize("speed, accepted", [
    (29.9, False), (30.0, True), (30.1, True), (179.9, True), (180.0, True), (180.1, False),
])
def test_set_speed_window_boundaries(cc, speed, accepted):
    cc.power_on()
    assert cc.set(speed) is accepted
    assert cc.state is (S.ACTIVE if accepted else S.STANDBY)


def test_resume_without_history_is_refused(cc):
    cc.power_on()
    assert cc.resume(100) is False


def test_resume_below_minimum_speed_is_refused(active):
    active.cancel()
    assert active.resume(20) is False and active.state is S.STANDBY


def test_accelerator_is_ignored_in_standby(cc):
    cc.power_on()
    cc.accelerator(True)
    assert cc.state is S.STANDBY


def test_cancel_in_off_is_a_noop(cc):
    cc.cancel()
    assert cc.state is S.OFF


# ---- exhaustive: every event in every state never crashes and keeps invariants -------
EVENTS = {
    "power_on": lambda c: c.power_on(),
    "power_off": lambda c: c.power_off(),
    "set": lambda c: c.set(100),
    "resume": lambda c: c.resume(100),
    "cancel": lambda c: c.cancel(),
    "accel_on": lambda c: c.accelerator(True),
    "accel_off": lambda c: c.accelerator(False),
}


@pytest.mark.parametrize("sequence", list(itertools.product(EVENTS, repeat=3)), ids="-".join)
def test_all_3_event_sequences_keep_invariants(sequence):
    cc = CruiseController()
    for name in sequence:
        EVENTS[name](cc)
        assert (cc.state is S.ACTIVE) == (cc.target is not None) or cc.state is S.OVERRIDE
        assert cc.control(100, 0.1) >= 0
        if cc.state is not S.ACTIVE:
            assert cc.control(50, 0.1) == 0.0


# ---- control law: system behaviour with a simple vehicle model -------------------------
@pytest.mark.requirement("REQ-CC-003")
def test_throttle_is_zero_unless_active(cc):
    assert cc.control(50, 0.1) == 0.0
    cc.power_on()
    assert cc.control(50, 0.1) == 0.0


def test_throttle_is_saturated_between_0_and_1(active):
    assert active.control(30, 0.1) == 1.0       # far below target -> full throttle
    assert active.control(150, 0.1) == 0.0      # above target -> no throttle


def test_integral_does_not_wind_up_during_saturation(active):
    for _ in range(1000):                       # stuck at 30 km/h for 100 s
        active.control(30, 0.1)
    assert active._integral == 0.0              # white-box check of the anti-windup rule
