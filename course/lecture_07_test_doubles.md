# Isolating the unit: testability and test doubles

## 7.1 Why isolate?

Production code rarely lives alone. `TemperatureSensor` reads an **ADC** (hardware), `InstrumentCluster` listens to a **bus** and reads the **clock**, and both call a **diagnostic manager**. If a test uses the real collaborators, then:

* it may be **impossible** (no hardware on the CI server);
* it is **slow** (real time passes, real I/O happens);
* it is **non-deterministic** (clock, noise, random);
* it cannot **force rare situations** (a short-to-ground; 100 ms of bus silence);
* when it fails you do not know **whose fault** it is.

The remedy is to replace collaborators by controllable stand-ins — **test doubles** — for the duration of the test.

## 7.2 Designing for testability: seams

You can only substitute what the code lets you substitute. A **seam** is a place where behaviour can be swapped without editing the code. The simplest and best seam is **dependency injection (DI)**: pass collaborators in instead of creating them inside.

```python
# verified: python
# Hard to test: the dependency is created inside, hidden.
import time
class ClusterBad:
    def is_stale(self, last_rx):
        return time.monotonic() - last_rx > 0.1     # real time -> must really wait

# Easy to test: the dependency is a parameter.
class ClusterGood:
    def __init__(self, clock):
        self.clock = clock
    def is_stale(self, last_rx):
        return self.clock.now() - last_rx > 0.1

from autotest.clock import FakeClock
clock = FakeClock()
cluster = ClusterGood(clock)
assert cluster.is_stale(0.0) is False
clock.advance(0.101)                                  # "wait" 101 ms instantly
assert cluster.is_stale(0.0) is True
```

The recurring seams in this course:

| Non-determinism / hardware | Injected as | Test replacement |
|---|---|---|
| Time | `clock.now()` | `FakeClock.advance()` |
| Hardware input | `ADC.read()` (a `Protocol`) | scripted / faulty ADC |
| Communication | bus object with `send` / `subscribe` | `VirtualCANBus` with fault hooks |
| Randomness | a seeded `random.Random(seed)` | fixed seed |

A `Protocol` (structural interface) such as `ADC` documents what the code *needs* from its collaborator; *anything* with a `read()` method — real driver, simulator, mock — qualifies. This is also the key to **SIL ↔ HIL** switching (Lab 13).

## 7.3 The taxonomy of test doubles

(Terminology follows Gerard Meszaros, *xUnit Test Patterns*.)

| Double | What it does | Verifies | Example |
|---|---|---|---|
| **Dummy** | fills a parameter, never used | nothing | a listener registered for an id that never occurs |
| **Stub** | returns canned answers | indirect *inputs* | `StubADC(0)`: forces "short to ground" |
| **Fake** | simplified *working* implementation | nothing itself | `FakeClock`, in-memory bus, a data-logger playing back samples |
| **Spy** | a real or fake object that **records** how it was used | afterwards, by inspection | `SpyADC.calls` counts conversions |
| **Mock** | pre-programmed with *expectations* and verifies them | indirect *outputs* (interactions) | `Mock(spec=DiagnosticManager).report.assert_called_with(...)` |

```python
# verified: pytest
import pytest
from autotest.sensors import SensorFault, TemperatureSensor

class StubADC:                       # STUB: a canned reading
    def __init__(self, counts): self.counts = counts
    def read(self): return self.counts

class SpyADC:                        # SPY: counts how it was used
    def __init__(self, counts): self.counts, self.calls = counts, 0
    def read(self):
        self.calls += 1
        return self.counts

def test_stub_forces_a_rare_fault():
    with pytest.raises(SensorFault, match="short to ground"):
        TemperatureSensor(StubADC(0)).read()

def test_spy_shows_one_conversion_per_call():
    spy = SpyADC(2000)
    sensor = TemperatureSensor(spy, filter_len=3)
    for _ in range(3):
        sensor.read_filtered()
    assert spy.calls == 3
```

## 7.4 State verification vs. interaction verification

There are two ways to judge a test:

* **State verification** — run the code, then check the *outcome*: a return value, the object's resulting state, the data on the bus. Resilient to refactoring.
* **Interaction (behaviour) verification** — check *which calls were made*: "`diag.report('U0121', failed=True)` was called". Necessary when the only observable effect **is** the call, but it ties the test to the implementation.

Two schools of thought exist ("classicist" vs "mockist"). A pragmatic rule that works well:

> **Prefer state verification with real, cheap, deterministic collaborators. Use stubs/fakes for slow or non-deterministic ones. Use mocks only when the interaction itself is the requirement.**

## 7.5 Using `unittest.mock` well

```python
# verified: python
from unittest import mock
from autotest.bus import VirtualCANBus
from autotest.diagnostics import DiagnosticManager
from autotest.ecu import DTC_COMM_LOST, InstrumentCluster
from autotest.clock import FakeClock

clock = FakeClock()
diag = mock.Mock(spec=DiagnosticManager)       # spec=: misspelled methods raise AttributeError
cluster = InstrumentCluster(VirtualCANBus(), clock, diag)

clock.advance(0.5)                              # 500 ms without a frame
assert cluster.displayed_speed() == "--"
diag.report.assert_called_with(DTC_COMM_LOST, failed=True)
print("interaction verified")
```

* **Always pass `spec=`** (or `autospec=True`). A bare `Mock()` accepts any attribute, so a typo in `assert_called_wiht` silently *passes* (newer Python versions reject names starting with `assert`, but typos in other names still slip through).
* `side_effect=[a, b, Exc()]` scripts a *sequence* of results and exceptions — perfect for "works twice, fails on the third read".
* `call_count`, `assert_called_once_with`, `assert_not_called` verify interactions.

### Patch where the name is *looked up*

`mock.patch("a.b.name")` replaces the attribute `name` **in module `a.b`**. A function imported with `from x import f` creates a *separate* reference in the importing module, so you must patch it *there*:

```python
# verified: python
from unittest import mock
from autotest.bus import VirtualCANBus
from autotest.ecu import WheelSpeedECU

# ecu.py does:  from .can import e2e_protect   -> the name now lives in autotest.ecu
with mock.patch("autotest.ecu.e2e_protect", return_value=b"\x00" * 5) as fake:
    bus = VirtualCANBus()
    WheelSpeedECU(bus).send_speed(50)
fake.assert_called_once()
assert bus.log[0].data == b"\x00" * 5          # the ECU used OUR function

with mock.patch("autotest.can.e2e_protect", return_value=b"\x00" * 5):
    bus = VirtualCANBus()
    WheelSpeedECU(bus).send_speed(50)
assert bus.log[0].data != b"\x00" * 5          # patched the wrong place: ECU still used the real one
```

In pytest the equivalent is `monkeypatch.setattr("autotest.ecu.e2e_protect", fake)`, undone automatically.

## 7.6 Faking time and randomness

* **Time:** inject a clock (as above). `time.sleep()` in tests makes them slow *and* flaky: too short and the test fails on a loaded machine, too long and the suite crawls.
* **Randomness:** inject a `random.Random(seed)` (or seed once and **print** the seed on failure) so a failing run can be replayed exactly. Hypothesis (Chapter 10) does this for you.

## 7.7 Fakes that grow into simulators

A fake bus that records frames and can **corrupt, drop or delay** them is both a test double *and* a fault-injection tool (Chapters 8 and 11). A fake ADC that plays back a recorded signal becomes a **replay** tool (Chapter 12). The same abstraction supports tests at several levels — a major payoff of designing seams once.

## 7.8 When test doubles go wrong

* **Over-mocking:** every collaborator mocked, assertions only on calls. The test re-states the implementation; any refactoring breaks it, and it proves only that the mocks were configured.
* **Doubles that diverge from reality:** the stub returns `None` while the real object raises. Prevent with `spec`/`autospec` and with *integration tests* (Chapter 8) that use the real thing.
* **Mocking what you don't own:** wrap third-party APIs in your own thin adapter and fake *that*.
* **Testing the mock:** if removing the code under test would still leave the test green, it tests nothing.

## Check your understanding

1. Classify: (a) a class returning `2048` for every `read()`; (b) `Mock()` asserting `report` was called once; (c) an in-memory bus; (d) an ADC object that counts reads.
2. Why does `mock.patch("autotest.can.e2e_protect")` not affect `autotest.ecu`'s calls to `e2e_protect`?
3. When is it appropriate to assert *interactions* instead of state?
4. How does dependency injection of a clock make a test both faster and *less* flaky than `time.sleep(0.11)`?

<!--ANSWERS-->
1. (a) stub; (b) mock; (c) fake; (d) spy.
2. `ecu.py` imported the name with `from .can import e2e_protect`, so it holds its own reference. Patching the original module changes a different binding; patch `autotest.ecu.e2e_protect` instead.
3. When the *call itself* is the externally required behaviour — e.g. "a DTC must be reported" and there is no other observable state — or when the collaborator is a boundary you must not actually invoke (sending a real message).
4. The fake clock advances instantly (no real waiting) and exactly (101 ms is precisely 101 ms), whereas `sleep` waits real time and its duration is subject to scheduler jitter on loaded machines.
