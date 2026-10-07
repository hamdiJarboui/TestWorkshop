# Lab 11 — Software-in-the-loop (SIL) simulation and acceptance criteria

> **Read first:** Chapter 14 — *Simulation, closed-loop testing and acceptance criteria* (`course/lecture_14_simulation_and_sil.md`).

**Duration:** 3 h · **Type:** closed-loop system testing / model-based testing · **Code under test:** `CruiseController` + `Vehicle`, `ABSController` + `QuarterCar`

## Why it matters
Controllers are only "correct" in a loop: the throttle value matters because of what the car then does. SIL runs the
production control code against a plant model long before a prototype exists; the same scenarios later run on HIL and in the car.

## Learning objectives
Turn requirements into **measurable acceptance criteria** (overshoot, settling time, dip, steady-state error, stopping distance);
**test the model too** (a wrong plant gives false confidence); use a *control group* (the scenario without ABS must fail);
run scenario sweeps; detect a controller whose tuning fails a requirement.

## Metrics used
| Metric | Definition | Criterion |
|---|---|---|
| Overshoot | (peak − target) / step | < 20 % (< 4 km/h on a 20 km/h step) |
| Settling time | last time outside ±1 km/h | < 25 s |
| Hill dip (5 %) | target − minimum after grade starts | < 4 km/h, full recovery |
| Steady-state error | after 120 s | < 0.1–0.5 km/h |
| ABS lock time | seconds with slip > 0.95 while v ≥ 5 m/s | = 0 |
| ABS distance | vs locked-wheel braking | ≥ 10 % shorter |

## Run it
```bash
pytest labs/lab11_sil_simulation -v
pytest -m sil
```

## Guided tour
* **Plant sanity tests first:** coasting, top speed, grade — if the model is wrong, everything downstream is noise.
* `test_baseline_without_abs_locks_the_wheel` — proves the scenario is hazardous, so "ABS prevents lock" is meaningful.
* Determinism test: fixed-step simulation ⇒ identical results every run (a prerequisite for regression testing).

## Exercises — `exercise_lab11.py`
8 % hill criteria (default tuning **fails** — find gains that pass) · ABS on ice · a 5 km/h biased speed sensor (what happens, what would detect it?).

## Debrief
* Your simulation passes. What *model assumptions* could still make the real car fail?
* Which scenarios would you add for a safety case (cut-in vehicle, sensor dropout mid-brake)?
* When does a SIL result transfer to HIL, and what must be re-validated?
