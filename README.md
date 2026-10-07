# Testing with Python — unittest, pytest & Automotive Software

A hands-on course in which you learn **every major kind of software testing** by testing realistic
automotive code (CAN bus, battery management, cruise control, ABS, diagnostics, tyre-pressure
monitoring) with Python's **`unittest`** and **`pytest`**.

* 13 labs + a capstone "bug hunt" (≈ 35 contact hours; see [COURSE_DESIGN.md](COURSE_DESIGN.md))
* Every lab: concept → fully worked, runnable examples → exercises → debrief questions
* A verified instructor solution for every exercise (`solutions/`), executed in CI
* No hardware needed: ECUs, sensors and vehicle dynamics are simulated; a switch shows how the same
  tests would run on a real bench (HIL)

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

make fast          # the everyday loop (≈ 3 s)
make lab N=06      # run one lab verbosely
pytest labs/lab02_pytest/exercise_lab02.py   # work on an exercise (fails until you finish it)
```

Windows without `make`: run the commands from the [Makefile](Makefile) directly (`python -m pytest ...`).

## Course map

| # | Lab | Testing type / technique | Main tools | Automotive case |
|---|-----|--------------------------|-----------|-----------------|
| 1 | [unittest fundamentals](labs/lab01_unittest/README.md) | **Unit testing** | `unittest.TestCase`, `subTest`, `setUp`, `assertRaises` | CAN frames, CRC-8, unit conversions, wheel-speed maths |
| 2 | [pytest fundamentals](labs/lab02_pytest/README.md) | Unit testing, fixtures, data-driven | `assert`, `parametrize`, fixtures, `tmp_path`, markers | Temperature sensor, BMS fault detection |
| 3 | [Black-box test design](labs/lab03_black_box/README.md) | **Equivalence classes, boundary values, decision tables** | `parametrize`, invariants | Battery charge-current derating |
| 4 | [Test doubles](labs/lab04_test_doubles/README.md) | **Isolation**: stub, fake, spy, mock, dummy | `unittest.mock`, `monkeypatch`, `FakeClock` | ADC hardware, diagnostics, timeouts without sleeping |
| 5 | [Integration testing](labs/lab05_integration/README.md) | **Integration / interface / contract** | virtual bus, fault hooks | Wheel-speed ECU → CAN → instrument cluster |
| 6 | [State machines & system tests](labs/lab06_state_machine/README.md) | **State-transition, functional/system, scenario** | exhaustive sequences | Cruise-control modes |
| 7 | [Property-based testing](labs/lab07_property_based/README.md) | **Property-based / generative** | Hypothesis | Signal codec round-trips, E2E protection, BMS safety invariants |
| 8 | [Robustness & fault injection](labs/lab08_robustness/README.md) | **Negative, fault-injection, fuzz, recovery** | seeded RNG, Hypothesis | Stuck sensors, bit errors, burst loss, fuzzing the UDS handler |
| 9 | [Regression & golden files](labs/lab09_regression_golden/README.md) | **Regression, snapshot/golden, log replay** | custom `golden` fixture | DTC reports, UDS transcripts, recorded drive cycle |
| 10 | [Performance & real-time budgets](labs/lab10_performance/README.md) | **Performance, timing, memory** | `perf_counter`, `tracemalloc` | 10 ms control cycle, saturated 500 kbit/s bus |
| 11 | [Simulation (SIL)](labs/lab11_sil_simulation/README.md) | **Closed-loop / model-based, acceptance criteria** | plant models | Cruise control on hills, ABS vs locked wheels |
| 12 | [Coverage & mutation](labs/lab12_coverage_mutation/README.md) | **Test-adequacy: coverage, mutation testing** | `pytest-cov`, `tools/mini_mutate.py` | "100 % covered" suite that catches nothing |
| 13 | [Acceptance, traceability, HIL](labs/lab13_acceptance_traceability/README.md) | **Acceptance (Given/When/Then), requirements traceability, SIL↔HIL** | custom marker + report | ISO 26262-style requirement → test matrix |
| ★ | [Capstone: TPMS bug hunt](capstone/README.md) | Everything | all of the above | Tyre-pressure monitoring; graded against 17 hidden defects |

### Which test types appear where?

| Test type | Labs | | Test type | Labs |
|---|---|---|---|---|
| Unit | 1, 2 | | Fuzz / negative | 7, 8 |
| Smoke / sanity | 2, 5 | | Fault injection / recovery | 5, 8 |
| Black-box design | 3 | | Regression / golden / replay | 9 |
| White-box (state, internals) | 6, 12 | | Performance / memory | 10 |
| Integration / contract | 5 | | Simulation (SIL) / HIL | 11, 13 |
| System / functional | 6, 11 | | Test adequacy (coverage, mutation) | 12 |
| Property-based | 7 | | Acceptance / traceability | 13 |

## Repository layout

```
src/autotest/        the software under test (the "ECU code")
  can.py             frames, signals, CRC-8, E2E protection     bms.py       battery management
  sensors.py         conversions + plausibility-checked sensor  cruise.py    cruise state machine + PI control
  bus.py             virtual CAN bus with fault injection       abs.py       ABS controller + quarter-car plant
  ecu.py             wheel-speed ECU + instrument cluster       vehicle.py   longitudinal vehicle model
  diagnostics.py     DTC debouncing + UDS-lite                  tpms.py      capstone SUT
  clock.py           SystemClock / FakeClock
labs/labNN_*/        README.md · worked tests (test_*.py) · exercise_labNN.py
capstone/            TPMS specification, starter suite, defect-injection grader
solutions/           instructor solutions (they run in CI, so they cannot rot)
tools/               mini_mutate.py (mutation tester), make_drive_log.py
docs/                requirements.csv, cheat sheet, instructor guide
conftest.py          shared fixtures (clock, bus, golden), --hil / --update-golden / --req-report
```

## How each lab is organised

1. **Read** the lab README (10 min) — the concept and why it matters in a vehicle programme.
2. **Run and read** the worked tests (`test_labNN_*.py`) — they are deliberately commented teaching material.
3. **Break something** — mutate the code under test and watch which test fails (this builds intuition for Lab 12 early).
4. **Do the exercises** in `exercise_labNN.py` (not collected by default; run the file explicitly).
5. **Debrief** with the discussion questions.

## Reference

* [docs/cheatsheet.md](docs/cheatsheet.md) — unittest ↔ pytest side-by-side, useful flags, marker recipes
* [docs/instructor_guide.md](docs/instructor_guide.md) — timing, answers, seeded defects, common misconceptions
* [docs/requirements.csv](docs/requirements.csv) — the requirement set used for traceability

> **Safety note.** The code here is teaching material, not production automotive software. The
> models are simplified; never use them for real vehicle decisions.
