"""Lab 12 exercises - kill the survivors found by mutation testing.

  Run it:       python course.py exercise 12
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the test.
  Done when:    `python course.py progress` shows every test of Lab 12 passing  AND the mutation commands below
                report no survivors for the targeted code.

Step 1 (terminal, no code): measure coverage of the earlier labs
    pytest labs/lab02_pytest labs/lab03_black_box --cov=autotest --cov-branch --cov-report=term-missing
    Which module has the lowest BRANCH coverage? Write down why 100 % is not the goal for every module.

Step 2 (terminal): find the weak spots of the cruise-control tests
    python tools/mini_mutate.py --target src/autotest/cruise.py --function control \\
        --tests labs/lab06_state_machine/test_lab06_state_machine.py labs/lab11_sil_simulation
    You should see 10/12 killed: two mutants in the PI arithmetic SURVIVE. Which assertion should have failed?

Step 3: write the tests below, then re-run Step 2 with this file ADDED to --tests:
        --tests labs/lab06_state_machine/test_lab06_state_machine.py labs/lab11_sil_simulation labs/lab12_coverage_mutation/exercise_lab12.py
    Goal: 12/12.
"""
import pytest

from autotest.cruise import CruiseController
from autotest.diagnostics import DiagnosticManager
from autotest.learn import todo


def test_pi_law_matches_a_hand_computed_sequence():
    """Kill the PI-arithmetic survivors with EXACT numbers computed by hand.

    Set-up: CruiseController(kp=0.05, ki=0.01), power_on(), set(100); speed is 90 km/h; dt = 0.1 s  ->  error = 10.
        u1 = kp*e + ki*(integral + e*dt) = 0.05*10 + 0.01*(0   + 1.0) = ?
        the integral then becomes 1.0, so u2 = ? and u3 = ?
    Hint 1: compute the three values on paper first.
    Hint 2: results = [cc.control(90, 0.1) for _ in range(3)];  assert results == pytest.approx([...])
    """
    todo("compute u1, u2, u3 by hand and assert them")


def test_healing_needs_exactly_the_configured_number_of_good_cycles():
    """DiagnosticManager(fail_threshold=1, heal_threshold=3): one failure activates the code; it must take EXACTLY 3 good cycles to heal.

    Hint 1: report failed=True once -> active_codes() == ["P0100"]
    Hint 2: report failed=False twice -> STILL active (2 good cycles are not enough);  a third -> not active any more.
    """
    todo("test the boundary of the healing counter")
