# Lab 8 — Robustness: negative testing, fault injection and fuzzing

> **Read first:** Chapter 11 — *Robustness and fault injection* (`course/lecture_11_robustness_and_fault_injection.md`).

**Duration:** 3 h · **Type:** robustness / fault-injection / fuzz · **Code under test:** sensor, bus, cluster, `DiagnosticManager.handle_request`, BMS

## Why it matters
Functional correctness answers "does it work?". Robustness answers **"does it fail safely?"** — the question behind
ISO 26262 safety mechanisms, ISO 21434 cybersecurity and the UDS diagnostic port that anybody with an OBD dongle can reach.

## Learning objectives
Inject sensor faults with a decorator (stuck, short, open); inject bus faults with seeded randomness; fuzz an input parser
and assert **universal** properties (never raises, always answers with a valid response); recognise hostile numerics
(NaN, ±inf); verify recovery and DTC history.

## Techniques
| Technique | Where |
|---|---|
| Fault-injection decorator (`FaultyADC`) | wraps any ADC |
| Bus fault hook with seeded RNG | `test_cluster_never_displays_an_invented_speed…` |
| Fuzzing: Hypothesis **and** a plain seeded loop | UDS handler |
| Documented gaps | stuck sensor is *not* detected today — the test says so |
| Strict `xfail` for known defects | **BUG-201 / BUG-202** below |

## Two real defects found by this lab
* **BUG-201** `max_charge_current(50, nan)` returns **100 A** — NaN fails every comparison, so no limit applies. *Safety-relevant.*
* **BUG-202** `evaluate([3.7, nan, 3.7], 25)` reports `NONE` (healthy).

They are pinned with `xfail(strict=True)`: the suite stays green now and goes **red when someone fixes the bug**, forcing the marker to be removed.
`solutions/bms_nan_fix.patch` is the verified fix.

## Run it
```bash
pytest labs/lab08_robustness -v -rx
```

## Exercises — `exercise_lab08.py`
*Run:* `python course.py exercise 8` — the tests start red (most with a `todo(...)` line: delete it when you start on that test). Hints are in each test's docstring; read them one at a time.

Fix BUG-201/202 and clean up the markers · TDD a "stuck sensor" plausibility check · model a 5-frame burst loss and show recovery.

## Debrief
* What does "fail-safe" mean for a charge-current limit when the temperature input is invalid?
* Why print/seed the RNG in fuzz tests?
* Fuzzing found nothing in the UDS handler. Does that prove it is secure? What *would* you need?
