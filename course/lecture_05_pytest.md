# pytest: concise, powerful tests

## 5.1 Why pytest

pytest is the de-facto standard for Python testing. It keeps the xUnit *ideas* (fixtures, isolation, discovery) but removes the ceremony:

* **plain `assert`** statements — pytest rewrites them to show exactly which values differed;
* **tests are functions** — classes are optional and need no base class;
* **fixtures** are injected by *name* instead of inherited, and compose freely;
* **parametrization** turns one test into a table of cases;
* **markers** categorise tests; **plugins** add coverage, property-based testing, parallel runs, reports.

It also runs `unittest.TestCase` suites unchanged, so adoption can be gradual.

## 5.2 Discovery and naming

By default pytest collects:

* files named `test_*.py` or `*_test.py`,
* inside them: functions named `test_*`, and methods named `test_*` of classes named `Test*` (no `__init__`).

```bash
pytest                       # everything under the current directory (or configured testpaths)
pytest tests/test_can.py     # one file (also works for files that don't match the pattern!)
pytest tests/test_can.py::test_crc[check-value]     # one test, by node id
pytest -k "crc and not slow" # name expression
```

## 5.3 Assertions with introspection

```python
# verified: pytest
import pytest
from autotest.bms import max_charge_current

def test_taper_at_90_percent():
    assert max_charge_current(90, 25) == pytest.approx(50.0)
```

When an assertion fails pytest shows the values it computed:

```
    def test_taper_at_90_percent():
>       assert max_charge_current(90, 25) == 60.0
E       assert 50.0 == 60.0
E        +  where 50.0 = max_charge_current(90, 25)
```

### Floats: `pytest.approx`
`assert x == pytest.approx(y)` compares with a tolerance (default relative 1e-6). Tune with `rel=` / `abs=`; it also works on lists and dicts.

### Exceptions: `pytest.raises`
```python
# verified: pytest
import pytest
from autotest.can import Signal

def test_value_above_maximum_is_rejected():
    sig = Signal("v", 0, 8, maximum=10)
    with pytest.raises(ValueError, match="above maximum") as info:
        sig.to_raw(11)
    assert "v" in str(info.value)       # inspect the exception afterwards
```

## 5.4 Fixtures: dependency injection for test set-up

A **fixture** is a function decorated with `@pytest.fixture`. A test (or another fixture) that lists its name as a parameter *receives its return value*:

```python
# verified: pytest
import pytest
from autotest.bms import BatteryManagementSystem

@pytest.fixture
def battery():
    bms = BatteryManagementSystem(capacity_ah=50, soc=50)
    yield bms                                   # --- test runs here ---
    assert 0 <= bms.soc <= 100                  # teardown: runs after EVERY test, even a failed one

def test_charging_is_clamped(battery):
    battery.update_soc(1000, 3600)
    assert battery.soc == 100

def test_discharging_is_clamped(battery):
    battery.update_soc(-1000, 3600)
    assert battery.soc == 0
```

Key mechanics:

* **Setup / teardown in one function:** code before `yield` is setup; after `yield` is teardown (it runs even when the test fails).
* **Composition:** a fixture may request other fixtures — pytest builds the dependency graph.
* **Fresh by default:** a function-scoped fixture is created per test, giving isolation without a base class.

### Scopes
`@pytest.fixture(scope=...)` controls how often the fixture is created:

| Scope | Created | Use for |
|---|---|---|
| `function` (default) | per test | anything mutable |
| `class` / `module` | once per class / file | expensive but **immutable** objects |
| `session` | once per run | e.g. a loaded signal database |

Wider scope = faster but riskier: if a test mutates a shared fixture, later tests see the mutation.

### Factories, autouse, conftest, parameters
```python
# verified: pytest
import pytest
from autotest.sensors import TemperatureSensor

class ScriptedADC:
    def __init__(self, *values): self.values = list(values)
    def read(self): return self.values.pop(0)

@pytest.fixture
def sensor_factory():                # "factory as fixture": the test chooses the data
    def make(*counts, filter_len=4):
        return TemperatureSensor(ScriptedADC(*counts), filter_len=filter_len)
    return make

def test_filter_averages(sensor_factory):
    s = sensor_factory(1024, 2048, 3072)
    for _ in range(3):
        last = s.read_filtered()
    assert last == pytest.approx(TemperatureSensor.T_MIN + 190 * 2048 / 4095)

@pytest.fixture(params=[0, 4095], ids=["short-to-ground", "open-circuit"])
def rail_value(request):             # a parametrized fixture: every test using it runs twice
    return request.param

def test_rails_are_faults(rail_value, sensor_factory):
    from autotest.sensors import SensorFault
    with pytest.raises(SensorFault):
        sensor_factory(rail_value).read()
```

* `autouse=True` makes a fixture run for every test in its scope without being requested (use sparingly: it is invisible at the call site).
* Fixtures placed in a file called **`conftest.py`** are available to all tests in that directory tree without imports — our course's shared `clock` and `bus` fixtures live in the root `conftest.py`.
* `pytest --setup-show` prints exactly when each fixture is set up and torn down — the quickest way to understand scopes.

## 5.5 Parametrization: tables of cases

```python
# verified: pytest
import pytest
from autotest.bms import BatteryManagementSystem, BMSFault

@pytest.mark.parametrize(
    "cells, temp, expected",
    [
        ([3.7, 3.7], 25, BMSFault.NONE),
        ([3.7, 4.21], 25, BMSFault.OVERVOLTAGE),
        ([3.7, 2.99], 25, BMSFault.UNDERVOLTAGE),
        ([3.7, 3.7], 61, BMSFault.OVERTEMPERATURE),
    ],
    ids=["healthy", "overvolt", "undervolt", "overtemp"],
)
def test_fault_detection(cells, temp, expected):
    assert BatteryManagementSystem().evaluate(cells, temp) is expected
```

Each row is reported as its own test (`test_fault_detection[overvolt]`), so a failure names the case. Additional features:

* **Stacking** two `parametrize` decorators produces the *cartesian product* (3 × 4 = 12 tests).
* `pytest.param(value, id="...", marks=pytest.mark.xfail(...))` attaches a marker or id to a single row.
* `indirect=True` routes a parameter through a fixture of the same name (useful to build objects from parameters).

Parametrization is how this course writes boundary-value and decision-table tests: **the table *is* the test design**, readable by a reviewer who has never seen Python.

## 5.6 Markers: classifying tests

```python
# verified: pytest
import pytest

@pytest.mark.smoke
def test_fast_sanity():
    assert 1 + 1 == 2

@pytest.mark.skipif(not hasattr(pytest, "approx"), reason="needs approx")
def test_conditional():
    assert True

@pytest.mark.xfail(reason="BUG-114: known rounding limitation", strict=True)
def test_known_bug():
    assert round(0.1 / 0.25) == 1      # rounds to 0 -> fails -> "expected failure"
```

* Select with `pytest -m smoke` or `pytest -m "not slow and not performance"`.
* **Register markers** (in `pyproject.toml`) and run with `--strict-markers` so a typo like `@pytest.mark.smok` is an error instead of a silently ignored label.
* `xfail(strict=True)` means "this *must* fail": if the bug gets fixed the run goes red, forcing someone to delete the marker. Non-strict `xfail` quietly turns into a pass.

## 5.7 Built-in fixtures you will use constantly

| Fixture | Gives you |
|---|---|
| `tmp_path` | a unique empty `pathlib.Path` directory per test |
| `monkeypatch` | safe, auto-undone `setattr`, `setenv`, `chdir`, `delattr` |
| `capsys` / `capfd` | captured stdout/stderr (`capsys.readouterr()`) |
| `caplog` | captured log records |
| `request` | introspect the requesting test (params, markers, config) |
| `pytestconfig` | access command-line options |

```python
# verified: pytest
import os

def test_tmp_path(tmp_path):
    f = tmp_path / "trace.asc"
    f.write_text("0.001 1 123 Rx d 3 01 02 03\n")
    assert f.read_text().startswith("0.001")

def test_monkeypatch(monkeypatch):
    monkeypatch.setenv("VEHICLE_VARIANT", "EV")
    assert os.environ["VEHICLE_VARIANT"] == "EV"     # restored automatically afterwards

def test_capsys(capsys):
    print("DTC U0121 set")
    assert "U0121" in capsys.readouterr().out
```

## 5.8 Configuration and options

Project-wide settings live in `pyproject.toml` (or `pytest.ini`). This course uses:

```toml
[tool.pytest.ini_options]
pythonpath = ["src", "."]
testpaths = ["labs", "solutions"]
addopts = "-ra --strict-markers --import-mode=importlib"
markers = ["smoke: fast sanity checks", "integration: ...", "slow: ..."]
```

Daily commands:

| Command | Purpose |
|---|---|
| `pytest -x` / `--lf` / `--ff` | stop at first failure / rerun last failures / failures first |
| `pytest -vv --tb=short` | verbose output, compact tracebacks |
| `pytest -rs -rx` | show reasons for skips and expected failures |
| `pytest --durations=10` | the ten slowest tests |
| `pytest --pdb` | open the debugger at a failure |
| `pytest --junitxml=report.xml` | machine-readable report for CI |
| `pytest --cov=pkg --cov-branch` | coverage (plugin `pytest-cov`) |

Useful plugins: `pytest-cov` (coverage), `hypothesis` (Chapter 10), `pytest-xdist` (parallel), `pytest-timeout`, `pytest-mock` (mock fixture), `pytest-bdd` (Gherkin scenarios), `pytest-html` (reports).

## 5.9 unittest or pytest?

| | unittest | pytest |
|---|---|---|
| Assertion style | `self.assertEqual(a, b)` | `assert a == b` |
| Fixtures | `setUp` / `tearDown` | injected, composable, scoped |
| Many inputs | `subTest` | `parametrize` with ids |
| Failure output | basic | introspected, with diffs |
| Ecosystem | standard library | large plugin ecosystem |
| Dependencies | none | one package |

A migration path that works: leave existing `TestCase` classes alone (pytest runs them), write *new* tests as plain functions, and convert old ones opportunistically.

## 5.10 Anti-patterns

* **Fixtures that hide the interesting setup.** If understanding a test requires opening three fixture files, inline the arrange step. Fixtures are for *shared* and *boring* setup.
* **Wide-scoped mutable fixtures** — hidden coupling between tests.
* **Logic in tests** (loops, `if`s computing the expected value) — the test can have its own bugs. Prefer tables of literal expected values.
* **Over-use of `autouse`.**
* **Asserting too much** in one test — the name stops describing the failure.

## Check your understanding

1. What does the code after `yield` in a fixture do, and when does it run?
2. How many tests are generated by two stacked `@pytest.mark.parametrize` decorators with 3 and 4 values?
3. Why register markers and use `--strict-markers`?
4. What is the difference between `xfail` and `xfail(strict=True)` when the bug gets fixed?

<!--ANSWERS-->
1. It is the teardown. It runs after the test that used the fixture, even if that test failed or errored.
2. 3 × 4 = 12 (the cartesian product).
3. Unregistered, a misspelled marker is silently accepted and the tests are never selected; with `--strict-markers` it is an immediate error.
4. A non-strict `xfail` quietly reports "XPASS" and the run stays green, so the marker lingers forever. Strict `xfail` makes the unexpected pass a *failure*, forcing the marker to be removed.
