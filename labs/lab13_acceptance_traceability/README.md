# Lab 13 — Acceptance tests, requirements traceability and SIL/HIL switching

> **Read first:** Chapter 16 — *Requirements, traceability, standards and continuous integration* (`course/lecture_16_requirements_traceability_ci.md`).

**Duration:** 3 h · **Type:** acceptance / requirements-based testing · **Artefacts:** `docs/requirements.csv`, `--req-report`

## Why it matters
Assessors (ISO 26262, ASPICE SWE.4–SWE.6) do not ask "do you have tests?" but **"show me which test verifies requirement X, and its result."**
Traceability — requirement ⇄ test ⇄ result — is the evidence package.

## Learning objectives
Write acceptance scenarios in **Given / When / Then** form; link tests to requirement IDs with a custom marker; produce a
traceability matrix; make the test suite **fail when a requirement has no test** or a test cites an unknown requirement;
run the same test body on a simulator and (optionally) on hardware.

## The mechanism (see `conftest.py`)
```python
@pytest.mark.requirement("REQ-BMS-003")      # on a test, class or module (pytestmark)
```
* `pytest --req-report` prints each requirement → PASS/FAIL with its tests.
* Meta-tests scan the repository: every ID in `docs/requirements.csv` needs ≥ 1 verifying test; every marker must cite a known ID.
* `@pytest.fixture(params=["sil", pytest.param("hil", marks=pytest.mark.hil)])` — `hil` tests are **skipped unless `--hil`**, so one test body serves simulator and bench.

## Run it
```bash
pytest labs/lab13_acceptance_traceability -v
pytest labs solutions -m "not slow" -q --req-report      # the matrix
pytest labs/lab13_acceptance_traceability --hil           # BenchADC raises: shows what a missing bench looks like
```

## Exercises — `exercise_lab13.py`
*Run:* `python course.py exercise 13` — the tests start red (most with a `todo(...)` line: delete it when you start on that test). Hints are in each test's docstring; read them one at a time.

1. **Requirements-driven development:** `REQ-TPMS-001/002` exist in the CSV but (without `solutions/`) nothing verifies them: the meta-test is red → write the tests → green.
2. An acceptance scenario for the dashboard during acceleration.
3. A second switchable back-end (`virtual` vs `pcan`) for the CAN tests.

## Debrief
* A requirement has 14 tests, another has 1. Is the second one less verified? What would you ask?
* PASS in the matrix, but the test never asserts on the requirement's *numbers*. How would an assessor catch that? (Hint: Lab 12.)
* What must change in a HIL back-end that is *not* just "a different class"? (timing, nondeterminism, safe state on test abort.)
