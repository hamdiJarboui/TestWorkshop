# Robustness and fault injection

## 11.1 Functional correctness is not enough

A function can be perfectly correct for valid input and still be dangerous because of what it does with **invalid, unexpected or hostile** input and **partial failure** of its surroundings. Safety engineers ask a different question from "does it work?": **"how does it fail?"**

* **Fail-safe** — on failure, go to a state that cannot cause harm (charging current → 0 A).
* **Fail-operational** — keep (degraded) service where stopping is itself dangerous (steering assistance continues in limp-home mode).
* **Fail-silent** — stop producing output so others can detect the loss.

Robustness testing verifies the *safety mechanisms* that implement these policies: input plausibility checks, E2E protection, timeouts, watchdogs, debounced diagnostics, safe states.

## 11.2 Fault models: what can go wrong

You cannot inject "everything"; you inject a **fault model** — a defined catalogue of failures. A useful starter catalogue:

| Where | Fault | Real-world cause | Typical expected reaction |
|---|---|---|---|
| **Sensor** | stuck-at (constant value) | frozen ADC, sensor fault | plausibility check, DTC |
| | short to ground / open circuit / short to supply | wiring | out-of-range reading → fault, substitute value |
| | noise, drift, offset (e.g. +5 km/h bias) | ageing, calibration | filtering, cross-checks |
| | NaN / out-of-range value | software, conversion | reject, safe value |
| **Bus** | corruption (bit flip) | EMI | CRC rejects frame |
| | loss (single, burst) | bus-off, overload | timeout, alive counter |
| | duplication, delay, re-ordering | gateway, congestion | alive counter, freshness check |
| | babbling idiot (flood) | stuck sender | filtering, bus guardian |
| **Power / time** | brown-out, reset mid-operation | start/stop | defined recovery, no half-written data |
| | clock jump, counter wrap | long run time | wrap-safe arithmetic |
| **Software** | exception, timeout, NaN | bugs | containment, safe state |

Each row is a test idea; each "expected reaction" is the oracle.

## 11.3 Injecting faults at the sensor: the decorator

A **fault-injection decorator** wraps a healthy source and corrupts it on demand — keeping the test setup identical for every fault:

```python
# verified: python
import pytest
from autotest.sensors import SensorFault, TemperatureSensor

class ConstADC:
    def __init__(self, v): self.v = v
    def read(self): return self.v

class FaultyADC:
    """Behaves normally for `after` reads, then injects the chosen fault."""
    def __init__(self, inner, mode, after=0):
        self.inner, self.mode, self.after, self.n, self.last = inner, mode, after, 0, None
    def read(self):
        value = self.inner.read(); self.n += 1
        if self.n <= self.after:
            self.last = value
            return value
        return {"stuck": self.last, "short_gnd": 0, "open": 4095}[self.mode]

for mode, message in [("short_gnd", "ground"), ("open", "open circuit")]:
    sensor = TemperatureSensor(FaultyADC(ConstADC(2000), mode, after=2))
    sensor.read(); sensor.read()                      # healthy period
    with pytest.raises(SensorFault, match=message):   # then the fault must be REPORTED
        sensor.read()
print("hard faults are reported, not converted into a temperature")
```

The *stuck-at* mode shows the value of tests as **documentation of gaps**: today a stuck sensor looks perfectly healthy to `TemperatureSensor` — a plausibility check is missing. A test can state that honestly (and drive the implementation: *test first*, then add "100 identical readings ⇒ `SensorFault('stuck')`").

## 11.4 Injecting faults at the bus, reproducibly

Random fault injection is powerful *if it is reproducible*: use a **seeded** random generator and print the seed.

```python
# verified: python
import random
from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.clock import FakeClock
from autotest.ecu import InstrumentCluster, WheelSpeedECU

def run(seed):
    rng, bus, clock = random.Random(seed), VirtualCANBus(), FakeClock()
    ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)

    def flip_a_bit_sometimes(frame):
        if rng.random() < 0.3:                                    # 30 % of frames get one bit flipped
            data = bytearray(frame.data)
            data[rng.randrange(len(data))] ^= 1 << rng.randrange(8)
            return CANFrame(frame.arbitration_id, bytes(data))
        return frame

    bus.add_fault(flip_a_bit_sometimes)
    sent = set()
    for _ in range(200):
        speed = float(rng.randrange(0, 250))
        sent.add(f"{speed:.0f}")
        ecu.send_speed(speed)
        clock.advance(0.01)
        shown = cluster.displayed_speed()
        assert shown == "--" or shown in sent, f"seed {seed}: invented value {shown}"   # the SAFETY property

for seed in range(5):
    run(seed)
print("under random bit errors the cluster never displayed an invented speed")
```

The oracle is a **safety property**, not an exact value: *whatever is displayed was actually sent.* That is exactly the guarantee E2E protection is supposed to give.

## 11.5 Negative tests: invalid input

Negative testing checks that invalid input is **rejected cleanly** (specific exception or error code), not silently accepted or crashing in an uncontrolled way. Be specific about the expected error — `pytest.raises(ValueError, match=...)` — because "raises *something*" also passes for a typo.

## 11.6 A case study: NaN

`NaN` ("not a number") is the classic hostile numeric. Every comparison with NaN is `False` — including `<` and `>` — so range checks written as `if x < low or x > high` let it **fall through**:

```python
# verified: python
import math
from autotest.bms import BatteryManagementSystem, max_charge_current

print("charge current at NaN temperature:", max_charge_current(50, math.nan), "A")
print("fault for a NaN cell voltage     :", BatteryManagementSystem().evaluate([3.7, math.nan, 3.7], 25))
```

At the time of writing this prints **100.0 A** and `BMSFault.NONE`: an *unknown* temperature allows full-rate charging, and an *unknown* cell voltage reports "healthy". Neither was in any requirement, yet both are safety-relevant — the kind of defect only a deliberate hostile-input probe finds (Lab 8). The correct policy is *fail-safe*: **unknown is not OK**. Either reject the input with an error or treat it as the most restrictive state.

Pinning a known defect with `xfail(strict=True)` keeps the suite green *today* and turns it red the day the bug is fixed, so the marker cannot be forgotten.

## 11.7 Recovery and "healing"

Safety mechanisms must also **recover**. Test the full cycle: *normal → fault → detection → safe state → fault removed → recovery*, and what the system **remembers** afterwards. In our diagnostics, a DTC becomes *inactive* after enough healthy cycles but remains *stored* as history until cleared — a requirement worth its own test.

## 11.8 Where faults are injected in industry

| Level | Mechanism |
|---|---|
| **Software** (this course) | decorators, hooks, mocks, mutating inputs |
| **Bus** | gateway or "rest-bus" simulator that drops/alters frames |
| **HIL** | fault-insertion units switch the pins of a real ECU (open circuit, short to ground/battery) |
| **Vehicle** | disconnecting connectors, controlled hazards on a proving ground |

Software-level injection is cheap, safe and repeatable, so do the bulk of it there; reserve HIL for physical effects.

## 11.9 Principles

* **Define the fault model and the expected reaction first** — otherwise "robust" means nothing.
* **Assert on safety properties** (never unsafe output) rather than exact values.
* **Seed and log** randomness; every failure must be replayable.
* **Verify detection, reaction *and* recovery** (and that diagnostics recorded it).
* Treat inputs from *anywhere outside the module* — sensors, buses, files, other software — as untrusted.

## Check your understanding

1. A function raises `ValueError` for NaN in one build and returns `0.0` in another. Are both acceptable for a charge-current limit? What is not acceptable?
2. What is the oracle in the "random bit errors" test, and why not an exact displayed value?
3. Why is `try: f(x) except ValueError: pass` a weak negative test?
4. List the three phases a recovery test should verify after a fault is injected and then removed.

<!--ANSWERS-->
1. Both are fail-safe (rejecting the input, or allowing 0 A). Returning the *full* current for an unknown temperature is not acceptable.
2. The oracle is a safety property: whatever the cluster shows must be a value that was actually sent (or `--`). Exact values cannot be predicted because which frames survive is random.
3. If `f(x)` raises nothing, the test still passes; and catching `ValueError` broadly hides whether the *right* error occurred. Use `pytest.raises(ValueError, match=...)`.
4. That the fault is *detected* (and reported), that the system moves to the *safe state / reaction*, and that after the fault is removed it *recovers* (and its history, such as stored DTCs, is retained appropriately).
