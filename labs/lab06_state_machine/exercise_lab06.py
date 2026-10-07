"""Lab 6 exercises - state-transition and scenario testing of the cruise controller.

  Run it:       python course.py exercise 6
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the
                test; the test then passes only if what you wrote is correct.
  Done when:    `python course.py progress` shows every test of Lab 6 passing.

Draw the state diagram first (see the Chapter 9 lecture): OFF -> STANDBY -> ACTIVE <-> OVERRIDE.
"""
import pytest

from autotest.cruise import CruiseController, CruiseState as S
from autotest.learn import todo
from autotest.vehicle import run_cruise


def drive_into(state):
    """Helper (given): return a controller that is in the named state."""
    cc = CruiseController()
    if state in ("standby", "active", "override"):
        cc.power_on()
    if state in ("active", "override"):
        cc.set(100)
    if state == "override":
        cc.accelerator(True)
    return cc


EVENTS = {                                  # helper (given): the 7 driver events
    "power_on": lambda c: c.power_on(),
    "power_off": lambda c: c.power_off(),
    "set": lambda c: c.set(100),
    "resume": lambda c: c.resume(100),
    "cancel": lambda c: c.cancel(),
    "accel_on": lambda c: c.accelerator(True),
    "accel_off": lambda c: c.accelerator(False),
}

# Exercise 1 - the COMPLETE transition table: 4 states x 7 events = 28 cells.
# Fill it from the specification (Chapter 9, section 9.2) - NOT by running the code and copying the output.
#                 power_on    power_off   set         resume      cancel      accel_on    accel_off
TABLE = {
    "off":      (S.STANDBY,  S.OFF,      S.OFF,      S.OFF,      S.OFF,      S.OFF,      S.OFF),   # (given)
    "standby":  (),          # TODO: 7 states
    "active":   (),          # TODO
    "override": (),          # TODO
}
# (zip without strict=: the rows are empty until you fill them in; see Hint 3 for a row-length check)
CASES = [(state, event, nxt) for state, row in TABLE.items() for event, nxt in zip(EVENTS, row)]  # noqa: B905


@pytest.mark.parametrize("state, event, expected", CASES)
def test_full_transition_table(state, event, expected):
    """Hint 1: cc = drive_into(state);  EVENTS[event](cc);  assert cc.state is expected
    Hint 2: remember `resume` only works in STANDBY with a saved target - drive_into("standby") has none.
    Hint 3: after you filled the table there must be 28 cases (4 rows x 7 events). A row with the wrong number of entries would
            silently drop cases - so add a test that asserts  len(row) == 7  for every row of TABLE.
    """
    todo("fill the TABLE (3 rows of 7) and write the 3-line body")


def test_overtaking_scenario():
    """Exercise 2 - a Given/When/Then scenario with the plant model.
        Given cruise is ACTIVE at 100 km/h
        When  the driver presses the accelerator for 5 s and then releases it
        Then  cruise is ACTIVE again with the SAME target, and the throttle after release stays below 0.5

    Hint 1: cc = CruiseController();  cc.power_on();  cc.set(100)
    Hint 2: trace = run_cruise(cc, 100, 60, events={20.0: lambda c, car: c.accelerator(True),
                                                   25.0: lambda c, car: c.accelerator(False)})
            (trace is a list of (time_s, speed_kmh, throttle))
    Hint 3: assert (cc.state, cc.target) == (S.ACTIVE, 100);  max(u for t, _, u in trace if t >= 25) < 0.5
    """
    todo("write the scenario")


def test_resume_above_max_speed():
    """Exercise 3 - a design question. What should resume() do when the car is already faster than 180 km/h?
    The spec is silent. CHOOSE a behaviour, write the test for it, and record the open question in a comment.

    Hint: set 100, cancel(), then resume(200): look at the return value and cc.target - is that what you want?
    """
    todo("choose, test, and document")
