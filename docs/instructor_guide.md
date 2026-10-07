# Instructor guide

## Before the course (30 min)
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
make solutions          # solutions + reference capstone score must be green / 17 of 17
make fast               # everyday loop
make req-report | tail  # traceability matrix, all PASS
```
Keep `solutions/` on an instructor branch. **Without `solutions/` the Lab 13 traceability meta-test is red for REQ-TPMS-001/002** — intended (Exercise 13.1), but tell learners.

## How the student workflow works
* Learners use `python course.py doctor | labs | lab N | exercise N | progress` (no `make`, no `PYTHONPATH`; `pip install -r requirements.txt` also installs the course library in editable mode).
* Every exercise test begins with `todo(...)`; deleting it is the learner's "I am starting this" gesture. `progress` counts passing tests per lab.
* **Lab 8 Exercise 1** asks learners to fix BUG-201/202 in `src/`; afterwards the two strict-xfail markers in the worked test go red *by design* — learners must delete them (see the lab README).
* **Lab 9** golden tests fail on their first run on purpose (they create the file); tell learners to read it and run again.
* **Lab 12**: the learner's tests are validated by re-running the mutation tool with the exercise file added (`12/12` and `8/8`).
* Before a course run, verify the exercises are *completable*: complete a few in a scratch copy (the instructor solutions show how) and run them.

## Timing and emphasis
| Lab | Time | Must land | Safe to trim |
|---|---|---|---|
| 1 | 2.5 h | AAA, `assertAlmostEqual`, `subTest`, `setUp` isolation | `load_tests`, `expectedFailure` |
| 2 | 3 h | fixtures (yield, scope), parametrize ids, `approx` | `capsys`, `monkeypatch.setenv` |
| 3 | 2.5 h | BVA both sides, decision-table interaction row | oracle-free grid test |
| 4 | 2.5 h | patch *where looked up*; fake clock; mock vs real | `dummy` |
| 5 | 3 h | contract test, fault hooks, seeded randomness | top-down/bottom-up theory |
| 6 | 3 h | draw the diagram first; invariants over sequences | white-box anti-windup test |
| 7 | 3 h | round-trip + invariant properties; shrinking demo | `st.data()` |
| 8 | 3 h | "fail safely", NaN finding, strict xfail | seeded fuzz loop |
| 9 | 2.5 h | bug-guard naming, golden review discipline, BUG-130 story | log-format details |
| 10 | 2.5 h | percentiles + ratios, why not means | `tracemalloc` |
| 11 | 3 h | acceptance criteria as numbers; test the model; control group | ABS maths |
| 12 | 2.5 h | coverage ≠ adequacy; equivalent mutants; read `mini_mutate.py` | ast details |
| 13 | 3 h | traceability, GWT, SIL/HIL parametrization | CSV scanning internals |

## Live-demo scripts (high payoff)
* **Lab 1 "Try this":** change `& 0xFF` to `& 0x7F` in `crc8`. Show which tests notice (catalogue value, bit-flip) and which do not.
* **Lab 7 shrinking:** remove `xfail` from `test_wrong_property_resolution_is_exact`; read the minimal counter-example.
* **Lab 9 revert the BUG-130 fix** in `ecu.py` (delete the `elif` branch): 3 tests turn red. Then restore.
* **Lab 12:** run the weak suite with `--cov` (100 %) and then `mini_mutate.py` (4 %).
* **Lab 8 strict xfail:** apply only the `src/autotest/bms.py` hunk of `solutions/bms_nan_fix.patch` (e.g. `filterdiff -i '*bms.py' solutions/bms_nan_fix.patch | patch -p1`, or edit by hand): the two `xfail(strict=True)` tests turn **red** (XPASS strict) — the suite forces the cleanup. Applying the *whole* patch also removes the markers, and the suite stays green.

## Answers to the "design question" exercises
* **Resume above 180 km/h (6.3):** current behaviour re-engages at the *saved* target; either is defensible — what matters is that the choice is a *recorded decision* with a test.
* **Empty cell list (3.3):** the spec is silent; raising is safer than reporting "healthy" with no data. Real answer: ask the product owner; ideally a distinct "no data" fault state.
* **Stuck sensor (8.2):** 100 identical filtered values is arbitrary — a real design would derive it from sensor noise floor and update rate.
* **Biased speed sensor (11.3):** the car settles at target + 5 km/h; integral action hides the error. Cross-plausibility (wheel speed vs GPS/engine speed) + DTC.
* **8 % hill (11.1):** defaults dip 5.4 km/h (fail); `kp=0.15, ki=0.02` gives 2.5 km/h and 9.6 s recovery. Discuss the trade-off (higher gains → more throttle activity/noise sensitivity).

## Defect catalogue
| ID | Where | Origin | Used in |
|---|---|---|---|
| BUG-087 alive-counter wrap | ecu.py | teaching scenario (fixed; guard test) | Lab 9 |
| BUG-093 CRC error refreshes timeout | ecu.py | teaching scenario | Lab 9 |
| BUG-114 resolution rounds 0.1 rpm to 0 | can.py | documented limitation | Labs 1, 2 |
| BUG-120 "valid=0 shows 0" | ecu.py | **not a bug** — cannot reproduce | Lab 9 |
| **BUG-130** corrupted frame costs two frames and sets a DTC | ecu.py | **found by Lab 9 replay; fixed** | Lab 9 |
| **BUG-201** NaN temperature → full charge current | bms.py | **found while writing Lab 8; open (strict xfail)** | Lab 8 |
| **BUG-202** NaN cell voltage → "healthy" | bms.py | **found while writing Lab 8; open (strict xfail)** | Lab 8 |
| **BUG-310** `LeakDetector.add` O(window), `VirtualCANBus.log` unbounded | tpms.py / bus.py | design flaws, open | Lab 10 |
| Redundant `soc >= 100` guard | bms.py | revealed by mutation analysis | Lab 12 |

## Capstone grading
`python capstone/grade.py --tests <their file>` prints caught/missed defects. 17 defects:
D01-D03 classification thresholds · D04 temperature compensation · D05-D08 sensor range limits · D09-D10 sensor-id validation ·
D11-D13 leak threshold / window edge / wrong extreme · D14 default nominal · D15 window length · D16 HIGH never reported · D17 samples never expire.
Likely blind spots (check these first when a score is low): the *inclusive range limits* (D05-D08), upper-casing (D10), and the window edge cases (D12, D15, D17).
Review the *tests*, not only the score: a suite that asserts `True` after calling everything can still catch crashes but never wrong values.

## Common misconceptions
* "More tests = better." → Lab 12.
* "A mock proves the interaction is right." → it proves the mock was called; Lab 4 debrief.
* "Hypothesis found nothing, so it's correct." → absence of counter-examples within the search budget.
* "Update the golden file to make the test green." → Lab 9.
* "Flaky test → add `sleep`/retry." → inject time; seed randomness.
* "Performance numbers on my laptop = target performance." → Lab 10 rule 5.

## Troubleshooting
| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError: autotest` | run from the repo root (pytest `pythonpath` is configured); for plain `unittest` use `PYTHONPATH=src` |
| golden test fails on first run | by design: it creates the file; re-run, then `git add` it |
| Hypothesis `FailedHealthCheck(filter_too_much)` | over-filtering with `assume()`; generate valid data directly (Lab 7) |
| `strict xfail` shows `XPASS(strict)` FAILED | the bug got fixed — remove the marker |
| mutation tool results differ between runs | stale `.pyc` — fixed with `PYTHONDONTWRITEBYTECODE=1`; if you modify the tool keep it |
| timing test flaky on a loaded CI box | rerun `-m performance` alone; widen the budget, never loosen to the mean |
| duplicate test module names | the repo uses `--import-mode=importlib`; keep unique names anyway |

## Verifying a change to the course
`make solutions && make fast && make performance && make slow` — all four must be green; then
`python capstone/grade.py` must still report 0/17 for the starter and 17/17 for the reference.
