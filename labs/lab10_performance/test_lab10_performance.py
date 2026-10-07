"""Lab 10 - performance and real-time budgets.

Rules for non-flaky performance tests in CI:
  * assert on percentiles / worst cases against GENEROUS budgets (10x headroom), never means
  * use time.perf_counter, warm up first, and repeat
  * prefer RELATIVE assertions (scaling, ratio to a baseline) over absolute wall-clock numbers
  * run them in a separate stage:  pytest -m performance   /   pytest -m "not performance"
"""
import gc
import statistics
import time
import tracemalloc

import pytest

from autotest.can import CANFrame, CANMessage, Signal, crc8, e2e_check, e2e_protect
from autotest.cruise import CruiseController
from autotest.ecu import WHEEL_SPEED_MSG

pytestmark = pytest.mark.performance


def measure(fn, repeat=2000, warmup=200):
    """Return per-call durations in seconds."""
    for _ in range(warmup):
        fn()
    gc.disable()          # avoid collector pauses polluting the sample
    try:
        out = []
        for _ in range(repeat):
            t0 = time.perf_counter()
            fn()
            out.append(time.perf_counter() - t0)
    finally:
        gc.enable()
    return out


def p(samples, pct):
    return statistics.quantiles(samples, n=1000)[int(pct * 10) - 1]


# ---- 1. real-time budget: the control task must fit its 10 ms cycle with margin -------------
@pytest.mark.requirement("REQ-CC-003")
def test_cruise_control_step_meets_its_10ms_cycle_with_big_margin():
    cc = CruiseController()
    cc.power_on()
    cc.set(100)
    samples = measure(lambda: cc.control(97.0, 0.01))
    budget = 0.010 * 0.10          # use at most 10 % of the cycle time (1 ms)
    assert p(samples, 99) < budget, f"p99={p(samples, 99) * 1e6:.1f} us"
    assert max(samples) < 0.010, "worst case must never miss the cycle deadline"


# ---- 2. throughput: can we keep up with a saturated 500 kbit/s bus? ---------------------------
def test_decoder_keeps_up_with_a_saturated_500kbit_bus():
    """A 500 kbit/s bus carries at most ~4 500 eight-byte frames/s: 111 bits per frame including
    intermission, BEFORE bit stuffing. Stuffing only lengthens frames (worst case ~135 bits,
    ~3 700 frames/s), so 4 500 is a safe upper bound for the decoder to keep up with."""
    frames = [e2e_protect(WHEEL_SPEED_MSG.encode({"speed_kmh": i % 300, "valid": 1}), i) for i in range(4500)]
    t0 = time.perf_counter()
    for i, raw in enumerate(frames):
        status, payload = e2e_check(raw, i)
        WHEEL_SPEED_MSG.decode(payload)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.5, f"decoded 1 s of worst-case bus traffic in {elapsed:.3f} s"


# ---- 3. scaling: cost must not grow with history length ------------------------------------------
def test_crc_cost_scales_linearly_with_length():
    short, long_ = bytes(8), bytes(8 * 50)
    t_short = statistics.median(measure(lambda: crc8(short), repeat=500))
    t_long = statistics.median(measure(lambda: crc8(long_), repeat=500))
    ratio = t_long / t_short
    assert ratio < 50 * 3, f"50x more data cost {ratio:.0f}x more time (expected ~50x, linear)"


# ---- 4. memory: tracemalloc ------------------------------------------------------------------------
def test_encoding_does_not_leak_memory():
    sig = CANMessage(1, "m", 2, (Signal("v", 0, 16, 0.1),))
    sig.encode({"v": 1.0})   # warm caches
    tracemalloc.start()
    before = tracemalloc.take_snapshot()
    for i in range(20000):
        sig.encode({"v": (i % 1000) * 0.1})
    after = tracemalloc.take_snapshot()
    tracemalloc.stop()
    growth = sum(s.size_diff for s in after.compare_to(before, "filename"))
    assert growth < 200_000, f"retained {growth} bytes after 20 000 encodes"


# ---- 5. finding the slow tests of the suite itself ------------------------------------------------------
def test_timing_is_part_of_the_report():
    """Run `pytest --durations=10` to list the slowest tests - a free performance monitor."""
    assert True
