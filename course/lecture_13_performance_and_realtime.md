# Performance, timing and resource testing

## 13.1 Non-functional requirements are requirements

A function that returns the right answer too late is wrong. In an ECU:

* A control task that needs 12 ms in a 10 ms cycle **misses its deadline** — a functional failure.
* A decoder that cannot keep up with a busy bus **drops frames**.
* A log that grows without bound **exhausts memory** after hours of driving.
* A search that is fine with 100 items but **quadratic** is unusable with 100 000.

Performance testing turns these into measurable, automated checks.

## 13.2 What to measure

| Quantity | Meaning | Automotive example |
|---|---|---|
| **Latency / execution time** | time for one operation | one `control()` step |
| **Throughput** | operations per second | frames decoded per second |
| **Jitter** | variation of a periodic event | spread of the 10 ms task start time |
| **Utilisation** | execution time ÷ period | 0.5 ms in a 10 ms task = 5 % CPU |
| **WCET** | worst-case execution time | upper bound used in schedulability analysis |
| **Memory** | RAM/stack/heap use, growth over time | log length, leaks |
| **Scalability** | how cost grows with input size | per-sample cost vs window length |

### Hard and soft deadlines
A **hard** real-time task must *never* miss its deadline (airbag, brake control): one miss is a failure. A **soft** task tolerates occasional misses with graceful degradation (infotainment). The strictness decides whether you test the **maximum** or a **high percentile**.

## 13.3 Statistics: never trust the mean

Timing data is skewed: most runs are fast, a few are slow (cache misses, garbage collection, a busy neighbour). The **mean hides the tail**.

| Statistic | Tells you | Use for |
|---|---|---|
| mean | typical cost (misleading) | rough comparison only |
| **median (p50)** | the usual case | trend tracking |
| **p95 / p99 / p99.9** | the tail | soft deadlines, SLAs |
| **max** | the worst observation | hard deadlines (but only a lower bound on the true WCET) |

## 13.4 A measurement helper

Good measurement discipline: **warm up** (first calls are slower), **repeat** many times, use a **monotonic high-resolution clock** (`time.perf_counter`, never `time.time`), and keep the **garbage collector** from pausing inside the sample.

```python
# verified: python
import gc, statistics, time
from autotest.cruise import CruiseController

def measure(fn, repeat=2000, warmup=200):
    for _ in range(warmup):
        fn()
    gc.disable()
    try:
        out = []
        for _ in range(repeat):
            t0 = time.perf_counter()
            fn()
            out.append(time.perf_counter() - t0)
    finally:
        gc.enable()
    return out

cc = CruiseController()
cc.power_on(); cc.set(100)
samples = measure(lambda: cc.control(97.0, 0.01))
q = statistics.quantiles(samples, n=1000)
p99, worst = q[989], max(samples)
print(f"median {statistics.median(samples)*1e6:.1f} us   p99 {p99*1e6:.1f} us   max {worst*1e6:.1f} us")

CYCLE = 0.010                                   # a 10 ms control task
assert p99 < 0.10 * CYCLE                        # use at most 10 % of the cycle: 10x headroom
assert worst < CYCLE                             # and never miss the deadline
```

### Rules for non-flaky performance tests
1. Assert **percentiles or maxima against generous budgets** (aim for ≥ 10× headroom on a developer PC), never a mean against a tight number.
2. Prefer **relative** checks (scaling ratios, comparison to a baseline) to absolute milliseconds.
3. Warm up, repeat, and exclude set-up from the timed region.
4. Run them in a **separate CI stage** (`pytest -m performance`) so parallel jobs do not disturb them.
5. Remember: a host PC measures **algorithmic** cost. The real **WCET** must be established on the target hardware (measurement plus static analysis).

## 13.5 Throughput: can we keep up?

A 500 kbit/s CAN bus carries at most about **4 500 eight-byte frames per second** (111 bit-times per frame including intermission, before bit stuffing; stuffing only lowers the rate). If the receiver pipeline cannot decode that many per second, frames will be lost under load — so test it:

```python
# verified: python
import time
from autotest.can import e2e_check, e2e_protect
from autotest.ecu import WHEEL_SPEED_MSG

frames = [e2e_protect(WHEEL_SPEED_MSG.encode({"speed_kmh": i % 300, "valid": 1}), i) for i in range(4500)]
t0 = time.perf_counter()
for i, raw in enumerate(frames):
    status, payload = e2e_check(raw, i)
    WHEEL_SPEED_MSG.decode(payload)
elapsed = time.perf_counter() - t0
print(f"decoded one second of saturated bus traffic in {elapsed*1000:.1f} ms")
assert elapsed < 0.5                              # generous: half a second for one second of traffic
```

## 13.6 Scalability: complexity regressions

The most common real performance defect is code whose cost **grows with data size**. Catch it by measuring at two sizes and comparing the **ratio**, not absolute times:

```python
# verified: python
import time
from autotest.tpms import LeakDetector

def per_call_cost(detector, fill, probe=200):
    for i in range(fill):                         # 1 kHz sampling: 'fill' ms of history inside the window
        detector.add(i * 0.001, 230.0)
    t0 = time.perf_counter()
    for i in range(probe):
        detector.add((fill + i) * 0.001, 230.0)
    return (time.perf_counter() - t0) / probe

small = per_call_cost(LeakDetector(), 500)
large = per_call_cost(LeakDetector(), 8000)
print(f"16x more history -> {large / small:.1f}x more time per sample")
assert large / small > 1.5                        # this detector recomputes max() over the whole window: O(window)
```

`LeakDetector.add` scans the entire 60 s window on every sample: at 1 kHz that is up to 60 000 elements per call. A monotonic-deque algorithm makes it O(1) amortised, and the *same ratio test* then proves the fix — Lab 10's exercise.

## 13.7 Memory and resource tests

Python's `tracemalloc` shows how much memory is allocated and by whom. Use it to catch **leaks** and **unbounded growth**:

```python
# verified: python
import tracemalloc
from autotest.bus import VirtualCANBus
from autotest.can import CANFrame

tracemalloc.start()
bus = VirtualCANBus()
for i in range(20_000):
    bus.send(CANFrame(0x100, bytes([i & 0xFF])))
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"{len(bus.log)} frames retained, {current / 1e6:.1f} MB")
assert len(bus.log) == 20_000 and current > 1_000_000      # BUG: the log is unbounded
```

The bus keeps every frame forever — fine for a short test, fatal in a gateway that runs for days. The cure is a **bounded buffer** (`collections.deque(maxlen=N)`) or opt-in logging, and the test that guards it asserts the *bound*.

Related resource checks: file-handle and thread leaks, stack depth (important on MCUs), and **soak tests** that run the system for hours.

## 13.8 Kinds of load testing

| Test | Question |
|---|---|
| **Load** | does it meet its budgets at the *expected* maximum load? |
| **Stress** | what happens *beyond* the limit — does it degrade gracefully or fail unsafely? |
| **Spike** | can it absorb a sudden burst (a flood of frames)? |
| **Soak / endurance** | does it stay healthy for hours (leaks, drift, counter wrap)? |

## 13.9 Finding the slow code: profiling

When a budget test fails, **profile** before optimising. `python -m cProfile -s cumtime script.py` shows where time goes; `pytest --durations=10` lists the suite's slowest tests (your own tests deserve performance monitoring too). Optimise the measured hot spot, then let the budget test confirm the gain.

## Check your understanding

1. A task has a 10 ms period and 4 ms worst-case execution time. What is its utilisation, and what test would you write for the deadline?
2. Why is asserting `mean < 5 ms` a weak performance test?
3. How do you detect a quadratic algorithm without relying on absolute timings?
4. What does a host measurement tell you and not tell you about target WCET?

<!--ANSWERS-->
1. 4/10 = 40 %. Measure the execution time repeatedly (warm-up first) and assert that the **maximum** (and a high percentile with headroom) is below the 10 ms deadline — on the target hardware for a genuine WCET.
2. The mean hides the slow tail; a few long executions can miss deadlines while the average looks fine.
3. Measure at two input sizes and compare the ratio of times with the ratio of sizes: a 16× larger input costing roughly 16× (or more) more per item is a red flag.
4. It exposes algorithmic and relative performance regressions, but the compiler, CPU, cache and RTOS of the target determine the real WCET, which must be measured/analysed there.
