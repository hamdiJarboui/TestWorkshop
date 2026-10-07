"""Lab 13 exercises. Run: pytest labs/lab13_acceptance_traceability/exercise_lab13.py -v"""
import pytest


# Exercise 1 - Requirements-driven development.
#   docs/requirements.csv already lists REQ-TPMS-001 and REQ-TPMS-002 (tyre pressure monitoring).
#   If the instructor's solutions/ folder is absent, the meta-test
#   `test_every_requirement_is_verified_by_at_least_one_test` is RED: no test verifies them yet.
#   Write tests for autotest.tpms (classify -> REQ-TPMS-001, LeakDetector -> REQ-TPMS-002) carrying
#   @pytest.mark.requirement("REQ-TPMS-00x") and watch the meta-test turn green.
#   Bonus: add REQ-TPMS-003 for sensor-id validation to the CSV yourself and repeat red -> green.
def test_new_requirement_gets_a_test():
    pytest.fail("TODO")


# Exercise 2 - Write acceptance scenario (Given/When/Then comments) for the cluster:
# "Given the engine is running and the bus is healthy, when the driver accelerates from 0 to
# 100 km/h in 10 steps, then the displayed speed never decreases." Mark it REQ-CLU-001.
def test_dashboard_never_goes_backwards_during_acceleration(bus, clock):
    pytest.fail("TODO")


# Exercise 3 - Extend `adc` fixture idea: write a `can_backend` fixture with params "virtual" and a
# hil-marked "pcan" that is skipped by default, then run the Lab 5 smoke test on both.
def test_backend_switch():
    pytest.fail("TODO")
