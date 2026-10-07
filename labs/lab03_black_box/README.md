# Lab 3 — Black-box test design

**Duration:** 2.5 h · **Type:** specification-based testing · **Code under test:** `bms.max_charge_current`, `BatteryManagementSystem.evaluate`

## Why it matters
You can never test all inputs (SOC × temperature is continuous). Test-design techniques choose the *few* inputs
most likely to expose defects. ISO 26262-6 explicitly recommends **equivalence classes** and **boundary value analysis** for
unit tests of safety-related software.

## Learning objectives
Derive tests from a specification **without reading the code**: equivalence partitioning, boundary value analysis (BVA),
decision tables, invariants/oracle-free checks.

## Techniques
| Technique | Idea | In this lab |
|---|---|---|
| Equivalence partitioning | inputs that the spec treats alike need one representative | temperature classes `<0`, `0..<10`, `10..45`, `>45` |
| Boundary value analysis | defects cluster at edges → test *on* and *either side* | −0.1/0/0.1, 9.9/10/10.1, 44.9/45/45.1 |
| Decision table | every combination of conditions → action | cold × taper × hot × full (note the *cold+taper interaction*) |
| Invariants | properties true for all inputs | 0 ≤ I ≤ rated; non-increasing in SOC |

## Run it
```bash
pytest labs/lab03_black_box -v
python tools/mini_mutate.py --target src/autotest/bms.py --function max_charge_current \
   --tests labs/lab03_black_box/test_lab03_black_box.py       # preview of Lab 12: 22/25 = 88 % (3 equivalent mutants)
```

## Exercises — `exercise_lab03.py`
BVA for the six fault limits of `evaluate`, a priority decision table for simultaneous faults, and the "spec is silent" case (empty list) — decide, justify, and log the question.

## Debrief
* Why test *both* sides of a boundary rather than only the boundary?
* The decision table has a row (cold + taper) that two single-condition tests would never reach. How did you find it?
* Which of your tests would still be valid if the implementation were rewritten completely? (That is the point of black-box.)
