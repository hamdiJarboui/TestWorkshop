"""Lab 9 exercises. Run: pytest labs/lab09_regression_golden/exercise_lab09.py -v"""
import pytest


# Exercise 1 - You receive bug report BUG-120: "cluster shows 0 instead of -- when the ECU
# sends valid=0 (speed invalid)". Reproduce it with a failing test FIRST, then fix
# src/autotest/ecu.py if needed. (Hint: read InstrumentCluster._on_frame carefully.)
def test_bug_120_invalid_flag():
    pytest.fail("TODO")


# Exercise 2 - Golden file for UDS: create golden/uds_session.txt that records requests and
# responses (hex) for: read DTCs, read VIN, clear DTCs, read DTCs again, unknown service.
def test_uds_session_transcript(golden):
    pytest.fail("TODO")


# Exercise 3 - Edit data/drive_cycle.log by hand (change one speed). Run the Lab 9 tests and read the
# diff produced by pytest. Revert via git. What is the danger of blindly running --update-golden?
