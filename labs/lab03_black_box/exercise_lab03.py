"""Lab 3 exercises - test design from a specification (no peeking at the code!).

  Run it:       python course.py exercise 3
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the
                test; the test then passes only if what you wrote is correct.
  Done when:    `python course.py progress` shows every test of Lab 3 passing.

SPECIFICATION - BatteryManagementSystem().evaluate(cell_voltages, temp_c) returns:
    OVERVOLTAGE      if any cell > 4.20 V
    UNDERVOLTAGE     if any cell < 3.00 V
    OVERTEMPERATURE  if temp_c > 60
    UNDERTEMPERATURE if temp_c < -20
    NONE             otherwise
  When several apply, the FIRST in this list wins (priority order).
"""
import pytest

from autotest.bms import BatteryManagementSystem, BMSFault
from autotest.learn import todo

bms = BatteryManagementSystem()
HEALTHY = [3.7, 3.7]


@pytest.mark.parametrize("cells, temp, expected", [
    ([4.20, 3.7], 25, BMSFault.NONE),             # ON the limit: still healthy      (given, as an example)
    ([4.21, 3.7], 25, BMSFault.OVERVOLTAGE),      # just beyond the limit: a fault   (given, as an example)
    # TODO: add the other 6 boundary cases: under-voltage (3.00 / 2.99), over-temperature (60 / 60.1),
    #       under-temperature (-20 / -20.1). Use HEALTHY for the cells when you test a temperature.
])
def test_boundaries(cells, temp, expected):
    """Boundary value analysis: test ON each limit (still OK) and JUST BEYOND it (fault).

    Hint: the body is one line:  assert bms.evaluate(cells, temp) is expected   (enums are compared with `is`)
    """
    todo("complete the table with 6 more rows, then write the assertion")


def test_priority_between_faults():
    """Design a small decision table for SIMULTANEOUS faults, write it as a comment, then test it as a parametrized test.

    Hint 1: e.g. cells [4.3, 2.9] are over- AND under-voltage; which fault does the spec say wins?
    Hint 2: also try over-voltage + over-temperature, and under-voltage + over-temperature.
    Hint 3: turn it into @pytest.mark.parametrize("cells, temp, expected", [...]) and fill 4 rows.
    """
    todo("write the table and the parametrized test (replace this function)")


def test_empty_cell_list():
    """The spec says NOTHING about an empty list of cells. Decide what SHOULD happen, test it, and explain why in a comment.

    Hint 1: is 'healthy' a safe answer when there is no data at all?
    Hint 2: look at what the code does now (pytest.raises(ValueError) is one defensible choice) and write down
            the question you would ask the product owner.
    """
    todo("choose a behaviour, justify it in a comment, assert it")
