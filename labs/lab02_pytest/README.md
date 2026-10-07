# Lab 2 — pytest fundamentals

> **Read first:** Chapter 5 — *pytest: concise, powerful tests* (`course/lecture_05_pytest.md`).

**Duration:** 3 h · **Type:** unit testing, data-driven testing · **Code under test:** `sensors.py`, `bms.py`, `can.py`

## Why pytest
Less boilerplate (plain `assert`), far better failure output, fixtures with dependency injection, parametrization, a plugin
ecosystem (coverage, Hypothesis, xdist, JUnit XML for CI) — and it runs `unittest` suites unchanged, so migration is gradual.

## Learning objectives
Use plain asserts and `pytest.approx`; assert exceptions with `pytest.raises(match=)`; build fixtures (yield teardown, fixtures
using fixtures, scopes); parametrize with ids; use `tmp_path`, `monkeypatch`, `capsys`; select tests with markers.

## Concepts
* **Fixture** = named, injected, reusable arrange step; teardown after `yield` always runs.
* **Scope:** `function` (default, safest) → `module` → `session` (only for immutable/expensive objects).
* **`parametrize`:** one test body × many data rows. Give rows `ids` so a failure names the case.
* **Markers:** `smoke`, `xfail(strict=True)`, `skipif` — `--strict-markers` (enabled here) rejects typos.

## Run it
```bash
pytest labs/lab02_pytest -v
pytest labs/lab02_pytest -v -m smoke
pytest labs/lab02_pytest -k "bms and not undervolt" -v
pytest labs/lab02_pytest --setup-show -k soc_clamped      # see fixture set-up/teardown
```

## Guided tour
Sections 1-5 of `test_lab02_pytest.py`: asserts → parametrization → fixtures → built-ins → markers.
Note `battery` fixture: its teardown asserts an **invariant** (SOC in 0..100) after *every* test using it — one fixture, free protection.

**Try this:** make one parametrized row wrong. Compare pytest's failure output to Lab 1's.

## Exercises — `exercise_lab02.py`
*Run:* `python course.py exercise 2` — the tests start red (most with a `todo(...)` line: delete it when you start on that test). Hints are in each test's docstring; read them one at a time.

1. Collapse two copy-pasted tests into one parametrized test.
2. Write a *factory fixture* (`sensor_factory`) and test the moving-average filter.
3. `parametrize` with `pytest.param(..., id=..., marks=xfail)` for charge current by SOC.
4. `tmp_path` + error cases for a calibration-file reader.

## Debrief
* When does a module-scoped fixture become a hidden coupling between tests?
* `xfail(strict=True)` vs `skip` — what does each tell the next engineer?
* Why is `pytest.approx` needed, and how do `rel` and `abs` differ?
