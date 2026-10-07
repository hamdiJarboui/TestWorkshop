"""Lab 6 exercises. Run: pytest labs/lab06_state_machine/exercise_lab06.py -v"""
import pytest

from autotest.cruise import CruiseController, CruiseState


# Exercise 1 - Draw a transition table (state x event -> next state) in a comment for ALL
# 4 states x 7 events, then implement it as ONE parametrized test with 28 rows.
def test_full_transition_table():
    pytest.fail("TODO")


# Exercise 2 - A scenario ("system test") in Given/When/Then style:
# Given the driver cruises at 100, When they overtake (accelerator pressed 5 s, released),
# Then cruise returns to ACTIVE with the SAME target and no throttle spike (< 0.5).
def test_overtaking_scenario():
    pytest.fail("TODO")


# Exercise 3 - Find a design question: what should resume() do when the car is above 180?
# Write the test for the behaviour you CHOOSE, and file the ambiguity as a comment.
def test_resume_above_max():
    pytest.fail("TODO")
