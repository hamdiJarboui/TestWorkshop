# Regression testing, golden files and replay

## 12.1 What regression means

A **regression** is behaviour that used to work and no longer does. Software changes constantly — new features, refactors, library updates, compiler upgrades — and every change can break something unrelated. **Regression testing** is re-running tests to detect that. Because a vehicle program lives for years and ships many variants, regression is where most automation pays for itself.

Three kinds of tests do regression duty:

1. The **whole existing suite**, run on every change (fast tests: every commit; slow ones: nightly).
2. **Bug-guard tests**: one test per fixed defect, so it can never silently return.
3. **Golden / snapshot and replay tests**: compare complex outputs with a trusted recording.

## 12.2 Bug-guard tests: the red–green discipline

When a defect is reported:

1. **Reproduce** it with a *failing* test (red). If you cannot reproduce it, you have not understood the report — it may even be invalid.
2. **Fix** the code until the test passes (green).
3. **Keep** the test forever, named after the ticket, with a docstring saying what broke and why.

```python
# verified: python
from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.clock import FakeClock
from autotest.ecu import InstrumentCluster, WheelSpeedECU

def test_bug_130_single_bit_error_must_cost_exactly_one_frame():
    """BUG-130: a CRC error left the expected alive counter unchanged, so the NEXT good
    frame failed the counter check too -> two lost frames and a DTC for ONE bit error."""
    bus, clock = VirtualCANBus(), FakeClock()
    ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)
    ecu.send_speed(10)
    bus.add_fault(lambda f: CANFrame(f.arbitration_id, bytes([f.data[0] ^ 1]) + f.data[1:]))
    ecu.send_speed(20)                       # corrupted in flight
    bus.clear_faults()
    ecu.send_speed(30)                       # must be accepted immediately
    assert cluster.displayed_speed() == "30"
    assert cluster.diag.stored_codes() == []

test_bug_130_single_bit_error_must_cost_exactly_one_frame()
print("bug guard passes on the fixed code")
```

**Prove the test is real:** temporarily revert the fix — the test must go red. A bug-guard test that cannot fail is worthless (Chapter 15 generalises this idea).

## 12.3 Golden-file (snapshot / approval) testing

Some outputs are too large or intricate to assert field by field: a diagnostic report, a UDS session transcript, a rendered dashboard timeline. A **golden file** stores the *approved* output; the test compares fresh output with it:

```
actual output ──► compare ◄── golden file (reviewed, in version control)
                    │
          equal → pass          different → fail, show the diff
```

The workflow depends on **discipline**:

* The first run *creates* the golden file; a human **reviews** it — it becomes a specification.
* When behaviour changes *intentionally*, regenerate it (`--update-golden`) and **review the diff in code review** — an updated golden file is a changed requirement, not a formality.
* Never "update to make it green" without understanding *why* it differs.

```python
# verified: pytest
from pathlib import Path
from autotest.diagnostics import DiagnosticManager

def assert_matches_golden(path: Path, actual: str, update=False):
    if update or not path.exists():
        path.write_text(actual)
        return
    assert actual == path.read_text(), f"differs from {path.name}; inspect then update deliberately"

def test_dtc_report(tmp_path):
    d = DiagnosticManager(fail_threshold=2, heal_threshold=2)
    for _ in range(2):
        d.report("U0121", failed=True)          # confirmed
    d.report("P0300", failed=True)               # pending only
    golden = tmp_path / "dtc_report.txt"
    assert_matches_golden(golden, d.export_report())     # first run: creates the golden file
    assert_matches_golden(golden, d.export_report())     # second run: compares
    assert "U0121 active=True stored=True" in golden.read_text()
```

**Make outputs deterministic** before snapshotting: no timestamps, no memory addresses, sorted collections. A golden file containing `2026-10-07 14:03:22` fails tomorrow.

## 12.4 Record and replay

Real vehicles produce **traces** (CAN logs in ASC/BLF/MDF format) of real drives. Replaying a recorded trace into a new software build and comparing the reaction with the previous release catches regressions nobody specified:

```python
# verified: python
from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.clock import FakeClock
from autotest.ecu import InstrumentCluster, WheelSpeedECU

# 1. RECORD: a few frames, in the format  <time_s> <can_id_hex> <data_hex>
rec_bus = VirtualCANBus()
ecu = WheelSpeedECU(rec_bus)
log, t = [], 0.0
for speed in (0, 20, 40, 60):
    ecu.send_speed(speed)
    f = rec_bus.log[-1]
    log.append(f"{t:.3f} {f.arbitration_id:03x} {f.data.hex()}")
    t += 0.01

# 2. REPLAY into a fresh system under test with a controlled clock
clock, bus = FakeClock(), VirtualCANBus()
cluster = InstrumentCluster(bus, clock)
seen = []
for line in log:
    ts, can_id, data = line.split()
    clock.advance(float(ts) - clock.now())
    bus.send(CANFrame(int(can_id, 16), bytes.fromhex(data)))
    seen.append(cluster.displayed_speed())

assert seen == ["0", "20", "40", "60"]          # 3. COMPARE with the approved transcript
print("replay transcript:", seen)
```

Lab 9's recorded drive cycle contains a deliberate corrupted frame; replaying it exposed BUG-130 — a defect no one had specified a test for.

## 12.5 Choosing which tests to re-run

When the suite is large:

| Strategy | Idea | Risk |
|---|---|---|
| **Retest all** | run everything | slow, but the safest |
| **Selection** | run only tests affected by the change (dependency analysis, coverage mapping) | misses indirect effects |
| **Prioritisation** | run most failure-prone / fastest tests first | still runs all eventually |
| **Tiering** | smoke on every commit, full unit/integration on merge, slow/HIL nightly | needs markers and discipline |

pytest markers (`smoke`, `slow`, `performance`) implement tiering with one command-line flag.

## 12.6 Flaky tests: the enemy of regression

A **flaky** test sometimes fails with no code change. Flakiness destroys trust: people learn to re-run and ignore red. Causes and cures:

| Cause | Cure |
|---|---|
| Real time (`sleep`, deadlines) | inject a fake clock |
| Randomness | seed it; log the seed |
| Test order / shared state | isolate with fresh fixtures; run in random order occasionally |
| Real I/O, network, shared files | fakes, `tmp_path` |
| Concurrency, race conditions | deterministic scheduling, explicit synchronisation |
| Resource limits on loaded CI | generous budgets; measure percentiles (Chapter 13) |
| Dirty environment (leftover files, ports) | per-test temp resources, cleanup |

**Never** "fix" flakiness with retries or longer sleeps without finding the cause: a flaky test is often a *real* race condition in the product.

## 12.7 Test data and logs under change

Recorded logs and golden files are **assets** that age:

* Store them in version control next to the tests, with a short README on how they were produced and how to regenerate them.
* Interfaces evolve: when a message layout changes, regenerate or migrate logs deliberately.
* Keep a few **minimised** traces (smallest log that reproduces a bug) rather than only huge ones.

## Check your understanding

1. In what order do you write the test and the fix for a reported defect, and what must you check about the test?
2. A golden-file test fails after a refactoring that should not change behaviour. What are your two options and which is almost always wrong?
3. Name three causes of flaky tests and the matching cure for each.
4. Why might replaying a recorded drive find defects that a requirement-based test suite does not?

<!--ANSWERS-->
1. Test first (it must fail, red), then the fix (green). Also verify the test fails without the fix — otherwise it guards nothing.
2. Either the refactoring really changed behaviour (find and fix it), or the golden file is outdated (regenerate it *after reviewing the diff*). Blindly regenerating to make it green is almost always wrong.
3. E.g. real time → fake clock; unseeded randomness → seed and log it; shared state/order dependence → isolated fixtures; real I/O → fakes or `tmp_path`.
4. Real traces contain situations nobody wrote a requirement for — odd timing, corrupted frames, sequences of events — so they exercise combinations that specification-based tests omit.
