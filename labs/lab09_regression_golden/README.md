# Lab 9 — Regression, golden-file and log-replay testing

> **Read first:** Chapter 12 — *Regression testing, golden files and replay* (`course/lecture_12_regression_testing.md`).

**Duration:** 2.5 h · **Type:** regression / snapshot / replay · **Code under test:** `InstrumentCluster`, `DiagnosticManager`

## Why it matters
Software changes continuously over a 7-year programme; every release must not re-break what was fixed. Replaying **recorded
drive cycles** (MDF/ASC logs) against new builds is how OEMs catch regressions that no one thought to specify.

## Learning objectives
Write bug-guard tests named after tickets; compare complex output with **golden files**; update goldens deliberately
(`--update-golden`) and review the diff; replay a recorded CAN log through the system.

## The workflow
1. A defect is reported → write a **failing** test that reproduces it.
2. Fix → test passes → keep it forever (named `test_bug_NNN_…`, docstring says what broke).
3. Complex outputs (reports, transcripts, dashboards over a drive) → golden file.
4. Changing a golden file is a **reviewed code change**, never a reflex.

## Run it
```bash
pytest labs/lab09_regression_golden -v
python tools/make_drive_log.py            # regenerate the recorded drive cycle
pytest labs/lab09_regression_golden --update-golden     # only after reading the diff!
```

## The finding behind this lab: BUG-130
Replaying `data/drive_cycle.log` (which contains one corrupted frame) showed the cluster discarding **two** frames, then
setting DTC U0100: the CRC-failed frame did not advance the expected alive counter. The fix is in `ecu.py`; the guard is
`test_bug_130_…`. Revert the fix (3 lines) and 3 tests go red — try it.

## Exercises — `exercise_lab09.py`
Triage BUG-120 (reproduce first — the report may be wrong!) · golden transcript of a UDS session · mutate the log and read the diff.

## Debrief
* What is the danger of `--update-golden` in a hurry? How does code review mitigate it?
* A golden file contains a timestamp. What happens in CI? How do you fix it?
* Where should recorded logs come from, and how do you keep them valid when the interface evolves?
