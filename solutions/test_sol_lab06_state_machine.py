"""Solutions - Lab 6 (state machine / system)."""
import pytest

from autotest.cruise import CruiseController, CruiseState as S
from autotest.vehicle import run_cruise

pytestmark = pytest.mark.system


def drive_into(state):
    cc = CruiseController()
    if state in ("standby", "active", "override"):
        cc.power_on()
    if state in ("active", "override"):
        cc.set(100)
    if state == "override":
        cc.accelerator(True)
    return cc


EVENTS = {
    "power_on": lambda c: c.power_on(), "power_off": lambda c: c.power_off(),
    "set": lambda c: c.set(100), "resume": lambda c: c.resume(100), "cancel": lambda c: c.cancel(),
    "accel_on": lambda c: c.accelerator(True), "accel_off": lambda c: c.accelerator(False),
}

#              power_on   power_off  set        resume     cancel     accel_on   accel_off
TABLE = {
    "off":      (S.STANDBY, S.OFF, S.OFF,      S.OFF,      S.OFF,     S.OFF,      S.OFF),
    "standby":  (S.STANDBY, S.OFF, S.ACTIVE,   S.STANDBY,  S.STANDBY, S.STANDBY,  S.STANDBY),
    "active":   (S.ACTIVE,  S.OFF, S.ACTIVE,   S.ACTIVE,   S.STANDBY, S.OVERRIDE, S.ACTIVE),
    "override": (S.OVERRIDE, S.OFF, S.ACTIVE,  S.OVERRIDE, S.STANDBY, S.OVERRIDE, S.ACTIVE),
}
CASES = [(st, ev, nxt) for st, row in TABLE.items() for ev, nxt in zip(EVENTS, row, strict=True)]


@pytest.mark.parametrize("state, event, expected", CASES, ids=[f"{s}-{e}" for s, e, _ in CASES])
def test_full_transition_table(state, event, expected):
    cc = drive_into(state)
    EVENTS[event](cc)
    assert cc.state is expected


def test_overtaking_scenario():
    # Given the driver cruises at 100 km/h
    cc = CruiseController()
    cc.power_on()
    cc.set(100)
    # When they overtake: accelerator pressed 5 s, then released
    trace = run_cruise(cc, 100, 60, events={20.0: lambda c, v: c.accelerator(True),
                                           25.0: lambda c, v: c.accelerator(False)})
    # Then cruise is ACTIVE again with the SAME target and no throttle spike
    assert (cc.state, cc.target) == (S.ACTIVE, 100)
    assert max(u for t, _, u in trace if t >= 25) < 0.5
    assert all(u == 0 for t, _, u in trace if 20 <= t < 25)


def test_resume_above_max():
    # DESIGN QUESTION (logged): resume at 200 km/h re-engages at the saved 100 km/h (the car then
    # coasts down) because the SAVED target is valid. Alternative: refuse above MAX_SET_SPEED.
    cc = CruiseController()
    cc.power_on()
    cc.set(100)
    cc.cancel()
    assert cc.resume(200) is True and cc.target == 100
