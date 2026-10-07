"""Lab 3 exercises. Run: pytest labs/lab03_black_box/exercise_lab03.py -v

Specification - BatteryManagementSystem.evaluate(cell_voltages, temp_c):
  returns OVERVOLTAGE if any cell > 4.20 V, UNDERVOLTAGE if any cell < 3.00 V,
  OVERTEMPERATURE if temp > 60, UNDERTEMPERATURE if temp < -20, else NONE.
  (Checks are made in that order of priority.)
"""
import pytest

from autotest.bms import BatteryManagementSystem, BMSFault


# Exercise 1 - Boundary values: list the 6 boundary cases (on / just beyond for each limit)
# and put them in a parametrized test. Use 4.20 +/- 0.01 etc.
def test_boundaries():
    pytest.fail("TODO")


# Exercise 2 - Decision table: write the table of the 4 interesting COMBINATIONS
# (over+under voltage, over-voltage+over-temp, ...) as a comment, then test the priority rule.
def test_priority_between_faults():
    pytest.fail("TODO")


# Exercise 3 - Invalid input: an empty list of cells. Decide from the spec what must happen
# and justify in a comment (is the spec silent? then raise a question to the 'product owner').
def test_empty_cell_list():
    pytest.fail("TODO")
