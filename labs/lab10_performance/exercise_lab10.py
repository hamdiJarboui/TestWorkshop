"""Lab 10 exercises. Run: pytest labs/lab10_performance/exercise_lab10.py -v"""
import time

import pytest

from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.tpms import LeakDetector


# Exercise 1 - SCALING BUG: LeakDetector.add() recomputes max() over its whole 60 s window.
# At 1 kHz sampling the window holds ~60 000 samples. Write a test that feeds 1 000 and then
# 20 000 samples (all inside the window) and compares the per-call time. Show the ratio.
# Then fix it with a monotonic deque (O(1) amortised) and prove the ratio shrinks.
def test_leak_detector_cost_does_not_grow_with_window_fill():
    pytest.fail("TODO")


# Exercise 2 - MEMORY BUG: VirtualCANBus.log keeps every frame forever. Use tracemalloc to show
# 200 000 sends retain tens of MB. Design the fix (bounded deque with maxlen? opt-in logging?)
# and justify it in a comment. Keep Lab 5 tests green.
def test_bus_log_is_bounded():
    pytest.fail("TODO")


# Exercise 3 - Write a "budget" fixture that wraps a block in perf_counter and fails the test
# if it takes longer than N seconds: `with budget(0.05): ...`. Use contextlib.contextmanager.
def test_budget_fixture():
    pytest.fail("TODO")
