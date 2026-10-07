"""Solutions - Lab 10 (performance)."""
import contextlib
import random
import time
import tracemalloc
from collections import deque

import pytest

from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.tpms import LeakDetector
from solutions.fast_leak import FastLeakDetector

pytestmark = pytest.mark.performance


@contextlib.contextmanager
def budget(seconds):
    t0 = time.perf_counter()
    yield
    elapsed = time.perf_counter() - t0
    assert elapsed < seconds, f"took {elapsed:.3f}s, budget {seconds}s"


def per_call_cost_at_fill(detector, fill, probe=300):
    for i in range(fill):                       # 1 kHz sampling: fill samples = fill ms, all in the window
        detector.add(i * 0.001, 230.0)
    t0 = time.perf_counter()
    for i in range(probe):
        detector.add((fill + i) * 0.001, 230.0)
    return (time.perf_counter() - t0) / probe


def test_original_leak_detector_cost_grows_with_window_fill():
    small = per_call_cost_at_fill(LeakDetector(), 500)
    large = per_call_cost_at_fill(LeakDetector(), 8000)
    assert large / small > 3, "documenting BUG-310: max() over the window makes add() O(window)"


def test_fast_leak_detector_cost_is_flat():
    small = per_call_cost_at_fill(FastLeakDetector(), 500)
    large = per_call_cost_at_fill(FastLeakDetector(), 8000)
    assert large / small < 3


def test_fast_detector_gives_identical_answers():
    rng = random.Random(7)
    slow, fast = LeakDetector(), FastLeakDetector()
    t, p = 0.0, 230.0
    for _ in range(3000):
        t += rng.uniform(0.0, 5.0)
        p = max(0.0, p + rng.uniform(-6, 5))
        assert slow.add(t, p) == fast.add(t, p)


# bounded bus log: opt-in capacity, default keeps full history (Lab 5 tests rely on it).
class BoundedBus(VirtualCANBus):
    def __init__(self, capacity):
        super().__init__()
        self.log = deque(maxlen=capacity)


def test_bus_log_is_bounded():
    tracemalloc.start()
    bus = BoundedBus(1000)
    for i in range(50_000):
        bus.send(CANFrame(0x100, bytes([i & 0xFF])))
    current, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert len(bus.log) == 1000 and current < 2_000_000


def test_budget_fixture_style_helper():
    with budget(0.5):
        sum(range(10_000))
    with pytest.raises(AssertionError, match="budget"):
        with budget(0.01):
            time.sleep(0.05)
