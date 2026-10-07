# Capstone — Tyre-Pressure Monitoring bug hunt

**Duration:** 4–6 h (individual or pairs) · **Uses:** every technique from Labs 1–13

## Scenario
You join a TPMS team. The module `src/autotest/tpms.py` has no tests. Your job: write a test suite that is
**good enough to catch regressions** — the team will later "refactor" the module, and your tests are the safety net.

## Specification (the only thing you may rely on)
Pressures in kPa, temperatures in °C.

| ID | Rule |
|----|------|
| S1 | Normalise to 20 °C: `p20 = p · 293.15 / (273.15 + T)` |
| S2 | Nominal pressure 230 kPa (overridable) |
| S3 | `p20 < 60 %` of nominal → **CRITICAL** |
| S4 | `60 % ≤ p20 < 80 %` → **LOW** |
| S5 | `80 % ≤ p20 ≤ 130 %` → **OK** |
| S6 | `p20 > 130 %` → **HIGH** |
| S7 | A drop of **≥ 20 kPa** within a **60 s** window (relative to the highest pressure in the window) → rapid-loss alarm |
| S8 | Sensor ids: exactly 8 hex digits, either case; invalid → `ValueError`; valid ids are returned **upper-case** |
| S9 | Readings outside 0…700 kPa or −40…125 °C → `ValueError` |

Requirements for traceability: **REQ-TPMS-001** (S3 critical), **REQ-TPMS-002** (S7 leak alarm).

## Deliverables
1. `capstone/test_tpms_student.py` (replace the starter; split into several files if you like).
2. Use **at least**: parametrization with ids · boundary value analysis · a fixture · one property-based test ·
   a `requirement` marker on the relevant tests · an equivalence-class argument in comments.
3. A short `capstone/REPORT.md` (≤ 1 page): your test strategy, what you did *not* test and why, the coverage figure,
   and which technique found the most.

## How you are graded
```bash
python capstone/grade.py              # injects 17 hidden defects one at a time; you must catch them
pytest capstone --cov=autotest.tpms --cov-branch --cov-report=term-missing
```
| Criterion | Weight |
|---|---|
| Defects caught (`grade.py` score) | 40 % |
| Suite is **green on the correct code** and deterministic (no sleeps, seeded randomness) | 15 % |
| Test design quality: boundaries, classes, readable names, one reason to fail | 20 % |
| Traceability + coverage evidence | 10 % |
| Report | 15 % |

The grader prints *symptoms* of missed defects (e.g. "classification wrong exactly at the LOW/OK threshold") — never the code
change — so you can iterate. Aim for 100 % (the instructor's reference suite scores 17/17).

## Hints (read only if stuck)
<details><summary>Hint 1</summary>For each threshold in S3–S6 test just-below / on / just-above at 20 °C where the float arithmetic is exact.</details>
<details><summary>Hint 2</summary>Limits in S9 are inclusive: test the limit itself <em>and</em> the next representable value beyond it, on both axes.</details>
<details><summary>Hint 3</summary>For S7 think about: exactly 20, just under 20, an old peak that should have expired, the window edge at exactly 60 s, and a gentle slope that adds up to a big drop over many minutes.</details>
<details><summary>Hint 4</summary>Mutation thinking: for every <code>&lt;</code>, <code>&lt;=</code>, constant and <code>max/min</code> in the spec, ask "which assertion fails if this is wrong?"</details>
