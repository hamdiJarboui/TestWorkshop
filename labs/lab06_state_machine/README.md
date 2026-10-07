# Lab 6 — State-transition and system-level testing

> **Read first:** Chapter 9 — *State-based and system-level testing* (`course/lecture_09_state_and_system_testing.md`).

**Duration:** 3 h · **Type:** state-based testing, functional/system testing · **Code under test:** `CruiseController`

## Why it matters
Mode logic (OFF / STANDBY / ACTIVE / OVERRIDE) is a classic place for hazardous bugs: cruise that stays active after braking,
or re-engages unexpectedly. Behaviour depends on *history*, so single-input tests are not enough.

## Learning objectives
Model behaviour as states × events; cover **all states, all valid transitions, all invalid events**; use an
exhaustive short-sequence test with invariants; test the control law (saturation, anti-windup) at the same time.

## Coverage levels
| Level | Meaning | Here |
|---|---|---|
| All-states | every state visited | covered by transition tests |
| 0-switch (all transitions) | every valid arrow taken | `test_off_to_standby` … `test_accelerator_overrides…` |
| Invalid-event coverage | every event in every state | exhaustive 3-event sequences (343 cases) + exercise 1's 28-row table |
| n-switch | sequences of n transitions | `itertools.product(EVENTS, repeat=3)` |

## Run it
```bash
pytest labs/lab06_state_machine -v -k "not sequences"
pytest labs/lab06_state_machine -q          # includes 343 generated sequence tests
```

## Guided tour
The state diagram is in the module docstring — **draw it before reading the tests**. Observe:
the sequence test asserts *invariants* (`ACTIVE ⇔ target is set`, throttle is 0 outside ACTIVE) instead of exact outputs,
so it can run over every sequence with no oracle for each one. `test_integral_does_not_wind_up…` is a deliberate **white-box** check.

## Exercises — `exercise_lab06.py`
28-row transition table · "overtaking" scenario in Given/When/Then with the plant model · a design question (`resume` above max).

## Debrief
* Which invalid transitions are *safety relevant* here? Would you want a DTC on them?
* What is the difference between asserting `state` and asserting the externally visible *behaviour* (throttle)?
* How many states/events before exhaustive sequence testing becomes impractical — and what do you do then?
