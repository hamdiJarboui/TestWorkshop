"""Solutions - Lab 12: tests written to kill specific mutation survivors.

Verify with:
  python tools/mini_mutate.py --target src/autotest/cruise.py --function control \
      --tests labs/lab06_state_machine/test_lab06_state_machine.py labs/lab11_sil_simulation solutions/test_sol_lab12_mutation.py
  python tools/mini_mutate.py --target src/autotest/diagnostics.py --function report \
      --tests labs/lab02_pytest labs/lab08_robustness solutions/test_sol_lab12_mutation.py
"""
import pytest

from autotest.cruise import CruiseController
from autotest.diagnostics import DiagnosticManager


def test_pi_law_matches_the_hand_computed_throttle_sequence():
    # target 100, speed 90, dt 0.1 -> error 10
    #   u1 = kp*e + ki*(I0 + e*dt) = 0.05*10 + 0.01*(0   + 1.0) = 0.51   (then I = 1.0)
    #   u2 = 0.5 + 0.01*(1.0 + 1.0) = 0.52 ;  u3 = 0.5 + 0.01*(2.0 + 1.0) = 0.53
    cc = CruiseController(kp=0.05, ki=0.01)
    cc.power_on()
    cc.set(100)
    assert [cc.control(90, 0.1) for _ in range(3)] == pytest.approx([0.51, 0.52, 0.53])


def test_pi_law_with_negative_error_uses_the_same_arithmetic():
    cc = CruiseController(kp=0.1, ki=0.0)
    cc.power_on()
    cc.set(100)
    assert cc.control(95, 0.5) == pytest.approx(0.5)
    assert cc.control(105, 0.5) == 0.0         # clamped, not negative


def test_healing_needs_exactly_the_configured_number_of_good_cycles():
    d = DiagnosticManager(fail_threshold=1, heal_threshold=3)
    d.report("P0100", failed=True)
    assert d.active_codes() == ["P0100"]
    d.report("P0100", failed=False)
    d.report("P0100", failed=False)
    assert d.active_codes() == ["P0100"]       # 2 good cycles are NOT enough
    d.report("P0100", failed=False)
    assert d.active_codes() == []              # the 3rd heals it
