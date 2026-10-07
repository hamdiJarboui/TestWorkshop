# Lab 10 — Performance and real-time budget testing

> **Read first:** Chapter 13 — *Performance, timing and resource testing* (`course/lecture_13_performance_and_realtime.md`).

**Duration:** 2.5 h · **Type:** performance / timing / memory · **Code under test:** `CruiseController.control`, codec, `LeakDetector`, `VirtualCANBus`

## Why it matters
A control task that takes 12 ms in a 10 ms cycle is a functional failure. A decoder that cannot keep up with a saturated
500 kbit/s bus drops frames. A log that grows forever crashes the gateway after 3 days of driving.

## Learning objectives
Build a measurement helper (warm-up, repeats, GC off, percentiles); express **budgets** instead of averages; test
**scaling** (does cost grow with history?) with ratios, not wall-clock numbers; check **memory** with `tracemalloc`;
keep performance tests from making CI flaky.

## Rules for non-flaky performance tests
1. Assert on **p99 / max** versus a **generous** budget (10× headroom), never on a mean.
2. Prefer **relative** assertions (ratio between sizes) over absolute milliseconds.
3. Warm up, repeat, disable GC while measuring.
4. Run in a separate CI stage (`pytest -m performance`) so parallel jobs do not disturb it.
5. Real worst-case execution time is measured **on target hardware** — host timing only catches algorithmic regressions.

## Run it
```bash
pytest labs/lab10_performance -v
pytest labs -m "not performance"          # exclude from the everyday loop
pytest --durations=10                     # the suite's own slowest tests
```

## Two real scalability defects (exercises)
* **`LeakDetector.add`** recomputes `max()` over the whole 60 s window → **O(window)** per sample; at 1 kHz that is 60 000 elements per call.
* **`VirtualCANBus.log`** is unbounded → memory grows without limit.

The instructor solutions demonstrate both (ratio > 3 before, < 3 after; bounded deque).

## Exercises — `exercise_lab10.py`
*Run:* `python course.py exercise 10` — the tests start red (most with a `todo(...)` line: delete it when you start on that test). Hints are in each test's docstring; read them one at a time.

Scaling test + monotonic-deque fix · `tracemalloc` + bounded log · a `budget(seconds)` context manager.

## Debrief
* Why is `time.time()` the wrong clock? Why disable GC?
* Your p99 is fine but max is 40× larger. Is that a problem for a hard real-time task? For a soft one?
* How would you move this test to the target ECU?
