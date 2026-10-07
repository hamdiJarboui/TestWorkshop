"""A deliberately BAD test suite: 100 % line and branch coverage of max_charge_current,
yet it would not notice most defects. (Not collected by default: name is not test_*.)

    pytest labs/lab12_coverage_mutation/weak_suite.py --cov=autotest.bms --cov-branch --cov-report=term-missing
    python tools/mini_mutate.py --target src/autotest/bms.py --function max_charge_current \
           --tests labs/lab12_coverage_mutation/weak_suite.py
"""
from autotest.bms import max_charge_current


def test_runs_every_branch_but_checks_almost_nothing():
    for soc, temp in [(50, -5), (50, 60), (50, 5), (50, 25), (100, 25), (90, 25)]:
        result = max_charge_current(soc, temp)
        assert result is not None
        assert result >= 0           # true for almost any mutant too


def test_invalid_input_path_is_executed_too():
    try:
        max_charge_current(101, 25)
    except ValueError:
        pass                         # executed, never verified that the right error is raised
