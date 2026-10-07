# Lab 7 — Property-based testing with Hypothesis

> **Read first:** Chapter 10 — *Property-based testing and fuzzing* (`course/lecture_10_property_based_and_fuzz.md`).

**Duration:** 3 h · **Type:** generative testing · **Code under test:** signal codec, E2E, `max_charge_current`

## Why it matters
Example-based tests check the cases *you* thought of. Property-based tests state a rule that must hold for **all** inputs;
Hypothesis generates hundreds of cases, then **shrinks** a failure to the smallest counter-example. It routinely finds the
`0x7FF` vs `0x800` kind of bug nobody listed.

## Learning objectives
Find properties (round-trip, invariant, idempotence, oracle/model, "never crashes"); write strategies (`st.floats`, `st.builds`,
`st.data`); control the search (`@settings`, `@example`, `assume`); read a shrunk failure.

## Property catalogue (automotive flavour)
| Pattern | Example |
|---|---|
| Round trip | `decode(encode(x)) ≈ x` within one resolution step |
| Detection guarantee | CRC detects *any* single-bit flip |
| Safety invariant | never charge below 0 °C or above 45 °C, whatever SOC |
| Monotonicity | charge current never increases with SOC |
| Reference model | a 10-line reference DTC debouncer vs the real manager (exercise 2) |
| Crash-resistance | `CANFrame(...)` either builds or raises `ValueError` — nothing else |

## Run it
```bash
pytest labs/lab07_property_based -v
pytest labs/lab07_property_based --hypothesis-show-statistics
pytest labs/lab07_property_based --hypothesis-seed=0       # reproduce a CI failure
```

## Guided tour
* `test_wrong_property_resolution_is_exact` is an `xfail` — remove the marker and read how Hypothesis shrinks a failure.
* The `assume()` anti-pattern: our first draft filtered two independent floats and Hypothesis raised `FailedHealthCheck(filter_too_much)`.
  The fix — generate the *delta* directly — is the rule: **generate valid data; don't filter invalid data**.

## Exercises — `exercise_lab07.py`
*Run:* `python course.py exercise 7` — the tests start red (most with a `todo(...)` line: delete it when you start on that test). Hints are in each test's docstring; read them one at a time.

Properties of `slip_ratio` · DTC debouncer vs a reference model · a `st.builds(CANFrame, ...)` strategy.

## Debrief
* Why is a round-trip property weaker than an example with a known byte string? What does each catch?
* Hypothesis stores failures in `.hypothesis/`. How should CI treat that directory?
* What makes a *good* property — and why is "output equals a re-implementation of the code" a bad one?
