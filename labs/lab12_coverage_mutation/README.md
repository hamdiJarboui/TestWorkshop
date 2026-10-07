# Lab 12 — Test adequacy: coverage and mutation testing

> **Read first:** Chapter 15 — *Test adequacy: coverage and mutation testing* (`course/lecture_15_test_adequacy.md`).

**Duration:** 2.5 h · **Type:** tests of the tests · **Tools:** `pytest-cov`, `tools/mini_mutate.py`

## Why it matters
ISO 26262 asks for structural coverage (statement → branch → MC/DC by ASIL). But **coverage only proves code *ran*, not that
anything *checked* it.** Mutation testing asks the real question: *if the code were wrong, would a test fail?*

## Learning objectives
Measure line/branch coverage and read the `term-missing` report; build a suite with 100 % coverage that is nearly worthless;
run a mutation tester and classify survivors as **weak test** or **equivalent mutant**; understand the cost/benefit of both metrics.

## Run it
```bash
pytest labs/lab12_coverage_mutation/weak_suite.py \
       --cov=autotest.bms --cov-branch --cov-report=term-missing      # full coverage, weak assertions
python tools/mini_mutate.py --target src/autotest/bms.py --function max_charge_current --tests labs/lab12_coverage_mutation/weak_suite.py
python tools/mini_mutate.py --target src/autotest/bms.py --function max_charge_current --tests labs/lab03_black_box/test_lab03_black_box.py
python tools/mini_mutate.py ... --list         # just list the mutants
pytest labs/lab12_coverage_mutation -v         # automated assertions about both scores (slow, ~25 s)
```

## What to expect
| Suite | Line+branch coverage of the function | Mutation score |
|---|---|---|
| `weak_suite.py` | 100 % | ≈ 4 % (1/25) |
| Lab 3 suite | 100 % | 22/25 — all three survivors are **equivalent mutants** |

**Equivalent mutants:** `soc >= 100 → soc > 100` (or `>= 101`) and `soc > 80 → soc >= 80` change the code but not the
behaviour — the taper formula already yields 0 A at 100 % and the full limit at 80 %. No test can kill them. They are not
noise: the explicit `soc >= 100` guard is **redundant code**, which a reviewer may now delete or document. Recognising
equivalent mutants is a human judgement call.

> **A tool bug worth knowing.** The first version of `mini_mutate.py` gave *non-deterministic* scores. Cause: Python validates
> cached bytecode by source mtime (whole seconds) and file size, so two same-length mutants written within one second
> (`100`→`101`) silently reused the previous mutant's `.pyc`. Fix: `PYTHONDONTWRITEBYTECODE=1` in the test subprocess.
> Lesson: when a test tool disagrees with itself, suspect the environment before the tests.

## How `mini_mutate.py` works (read it — it is ~120 lines)
Parses the target with `ast`, enumerates mutation sites (comparison/arithmetic/boolean operators, numeric constants),
rewrites one site at a time in a scratch copy of the project, runs pytest, and counts a mutant as *killed* if the run fails.

## Exercises — `exercise_lab12.py` (terminal work)
Find the lowest-branch-coverage module · classify survivors of `CruiseController.control` (state-machine suite: 8/12; + SIL suite: 10/12 — which exact PI arithmetic is still unchecked?) · write one test that kills the most
survivors in `DiagnosticManager.report` · argue why 100 % mutation score is not a sensible CI gate.

## Debrief
* Can you reach 100 % branch coverage with a test that has no assertions? (Open `weak_suite.py`.)
* Why is MC/DC stricter than branch coverage, and which classes of defect does it target?
* Where would you spend a limited test budget: raising coverage 90→100 %, or mutation score 60→80 % on the safety core?
