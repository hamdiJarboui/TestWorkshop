"""Lab 12 exercises (run in a terminal, answers go in comments / a short report).

1. Measure: pytest labs/lab02_pytest labs/lab03_black_box --cov=autotest --cov-branch --cov-report=term-missing
   Which module has the lowest BRANCH coverage? Write 2 tests to raise it - and say why 100 %
   is not the goal for every module.
2. Mutate:  python tools/mini_mutate.py --target src/autotest/cruise.py --function control \
              --tests labs/lab06_state_machine/test_lab06_state_machine.py
   (expect 8/12). Add the simulation suite:  --tests labs/lab06_state_machine/test_lab06_state_machine.py labs/lab11_sil_simulation
   (expect 10/12). Two PI-arithmetic mutants STILL survive: even closed-loop tests only check
   behaviour in broad strokes. Classify each survivor: (a) weak test -> write a unit test with an
   exact hand-computed throttle value for CruiseController(kp=0.05, ki=0.01) that kills them,
   or (b) equivalent mutant -> explain why.
3. Mutate diagnostics:  --target src/autotest/diagnostics.py --function report \
              --tests labs/lab02_pytest labs/lab08_robustness
   Two survivors remain (both in the healing counters). Write ONE new test that kills both.
   Which technique from Labs 3/7 finds it fastest?
4. Discuss: why is a mutation score of 100 % impossible/undesirable as a hard CI gate?
"""
import pytest


def test_placeholder():
    pytest.fail("TODO: complete the exercises above in a terminal")
