"""Lab 10 exercises - performance: scaling, memory, a budget helper.

  Run it:       python course.py exercise 10
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the test.
  Done when:    `python course.py progress` shows every test of Lab 10 passing.
Timing tests: use GENEROUS limits and ratios, never tight absolute numbers (see Chapter 13).
"""
import contextlib
import time
import tracemalloc
from collections import deque

import pytest

from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.learn import todo
from autotest.tpms import LeakDetector


def per_call_cost(detector, fill, probe=300):
    """Helper (given): average seconds per add() after `fill` samples (1 kHz sampling) are already in the window."""
    for i in range(fill):
        detector.add(i * 0.001, 230.0)
    t0 = time.perf_counter()
    for i in range(probe):
        detector.add((fill + i) * 0.001, 230.0)
    return (time.perf_counter() - t0) / probe


def test_leak_detector_cost_grows_with_window_fill():
    """Exercise 1 - LeakDetector.add() recomputes max() over its whole 60 s window, so it gets slower as the window fills.
    Prove it with a RATIO, not an absolute time.

    Hint 1: small = per_call_cost(LeakDetector(), 500);  large = per_call_cost(LeakDetector(), 8000)
    Hint 2: 16x more history should make each call clearly slower: assert large / small > 3
    Stretch: write a faster detector (a monotonic deque keeps the maximum at the front: O(1) amortised), and show the SAME ratio
    test now gives < 3 for your version while both versions return identical alarms on random data.
    """
    todo("measure at two sizes and assert on the ratio")


class BoundedBus(VirtualCANBus):
    """A bus whose log keeps only the last `capacity` frames."""

    def __init__(self, capacity):
        super().__init__()
        # TODO: replace self.log by a deque with maxlen=capacity
        todo("use collections.deque(maxlen=capacity)")


def test_bounded_bus_keeps_memory_flat():
    """Exercise 2 - VirtualCANBus.log keeps EVERY frame forever (a leak in a long-running gateway). Fix it in BoundedBus and prove it.

    Hint 1: tracemalloc.start();  bus = BoundedBus(1000);  send 50_000 frames;  current, _ = tracemalloc.get_traced_memory();  tracemalloc.stop()
    Hint 2: assert len(bus.log) == 1000 and current < 2_000_000
    """
    todo("write the memory test")


@contextlib.contextmanager
def budget(seconds):
    """Exercise 3 - a context manager that FAILS if the block takes longer than `seconds` of wall time.

    Hint: t0 = time.perf_counter();  yield;  elapsed = time.perf_counter() - t0;  assert elapsed < seconds, f"took {elapsed:.3f}s, budget {seconds}s"
    """
    todo("implement the budget helper")
    yield


def test_budget_helper_works():
    """Use it twice: a fast block passes, and a slow one (time.sleep(0.05) with budget 0.01) raises AssertionError.
    Hint: with pytest.raises(AssertionError, match="budget"):  with budget(0.01): time.sleep(0.05)
    """
    todo("test the helper")
