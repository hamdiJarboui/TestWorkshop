# Integration testing: where components meet

## 8.1 What goes wrong between components

Unit tests prove each part works **in isolation against its own assumptions**. Integration defects are mismatches between those assumptions:

| Mismatch | Example | Visible only when connected |
|---|---|---|
| **Data layout** | sender: speed in bytes 2–3 little-endian; receiver reads big-endian | ✔ |
| **Scaling / units** | factor 0.01 vs 0.1; m/s vs km/h | ✔ |
| **Protocol state** | alive counter wraps at 16; receiver expects 255 | ✔ |
| **Timing** | sender cycle 20 ms, receiver timeout 15 ms | ✔ |
| **Error handling** | sender sends `valid=0`, receiver ignores the flag | ✔ |
| **Sequencing** | one corrupted frame disturbs *two* receptions (BUG-130, Lab 9) | ✔ |

Each side's unit tests can be green while the system is wrong. Integration tests exist to catch exactly these.

## 8.2 Integration strategies

| Strategy | Idea | Pros | Cons |
|---|---|---|---|
| **Big bang** | connect everything, then test | no scaffolding | failures cannot be localised |
| **Bottom-up** | integrate leaves first (codec → ECU → bus → cluster) using *drivers* | early confidence in basics | UI/top logic tested late |
| **Top-down** | start with the top component, *stub* the lower ones | early view of overall flow | many stubs |
| **Sandwich** | both directions, meeting in the middle | balanced | more planning |
| **Risk-based** | integrate the riskiest interface first | effort goes where defects are likely | needs a risk analysis |

Choose by **risk**: interfaces with safety relevance, many teams, or complex timing deserve the earliest and heaviest testing.

## 8.3 A virtual bus as the integration environment

Our `VirtualCANBus` connects nodes the way a real bus does — `send(frame)` delivers to subscribers filtered by identifier — and adds two testing features:

* a **log** of every frame (like a bus logger);
* **fault hooks**: functions that may return a *modified frame* (corruption) or `None` (loss).

```python
# verified: python
from autotest.bus import VirtualCANBus
from autotest.clock import FakeClock
from autotest.ecu import InstrumentCluster, WheelSpeedECU

bus, clock = VirtualCANBus(), FakeClock()
ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)

ecu.send_speed(87.4)
assert cluster.displayed_speed() == "87"            # the smoke test: it works end to end

clock.advance(0.099); assert cluster.displayed_speed() == "87"     # just inside the 100 ms timeout
clock.advance(0.002); assert cluster.displayed_speed() == "--"     # just outside
print("timing boundary verified without sleeping")
```

## 8.4 Interface and contract tests

An **interface specification** is a contract: *which frame, which bytes, which scaling, how often.* A **contract test** pins the contract itself by asserting the exact bytes on the wire:

```python
# verified: python
from autotest.bus import VirtualCANBus
from autotest.ecu import WHEEL_SPEED_MSG, WheelSpeedECU

bus = VirtualCANBus()
WheelSpeedECU(bus).send_speed(100.0)
frame = bus.log[0]

assert frame.arbitration_id == 0x1A0
assert frame.data.hex() == "d000102701"     # crc=d0 counter=00 speed=0x2710 (10000 × 0.01) valid=1
assert WHEEL_SPEED_MSG.signals[0].factor == 0.01
print("contract holds:", frame.data.hex())
```

Why is this better than a round-trip test (encode then decode)? A round trip passes even if *both* sides change the scaling the same wrong way. Only a test against **independent, written-down bytes** detects an accidental contract change before the other team does. In industry, the independent source is the signal database (DBC/ARXML) and recorded traces.

## 8.5 Fault injection at the interface

The bus is the natural place to inject faults, because real buses *do* corrupt, lose and duplicate frames:

```python
# verified: python
from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.clock import FakeClock
from autotest.ecu import InstrumentCluster, WheelSpeedECU

bus, clock = VirtualCANBus(), FakeClock()
ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)

ecu.send_speed(50)                                               # a good frame
bus.add_fault(lambda f: CANFrame(f.arbitration_id, bytes([f.data[0] ^ 0xFF]) + f.data[1:]))
ecu.send_speed(120)                                              # CRC byte corrupted "in flight"
assert cluster.displayed_speed() == "50"                         # the cluster kept the last GOOD value
bus.clear_faults()
ecu.send_speed(130)
assert cluster.displayed_speed() == "130"                        # and recovered immediately
```

This verifies a **safety mechanism end to end**: the receiver *rejects* corrupted data and does not display an invented value. Lab 8 repeats this with random, seeded bit errors; the chapter on robustness (Chapter 11) generalises it.

## 8.6 Smoke tests

A **smoke test** is a tiny end-to-end check that the system is fundamentally alive — one frame in, one number out. It runs first (`pytest -m smoke`), takes milliseconds, and answers "is it worth running the rest?" Name them and keep them few.

## 8.7 Timing in integration tests

Timing behaviour (timeouts, cycle times, debounce) is a major source of integration defects and a major source of **flaky** tests if done with real sleeps. Inject the clock and test **both sides of every limit**: just under the timeout (still valid) and just over it (invalid). The same method scales to supervision timers, watchdogs and E2E timeouts.

## 8.8 Practical advice

* Keep integration tests **few and meaningful**; each runs more code, so each failure is harder to localise. When one fails, **write a unit test that reproduces it** at the lowest level you can.
* Assert on **observable behaviour** at the interface (frames, displayed value, DTCs), not on private state.
* Share the environment (virtual bus, recorded traces) with later levels — the same scenarios run on a **rest-bus simulation** against a real ECU on the bench.
* Test **negative interface behaviour** too: wrong length, wrong identifier, `valid=0`, stale data.

## Check your understanding

1. Give two integration defects that cannot be found by unit-testing each side separately.
2. Why is a contract test (exact bytes) stronger than an encode/decode round-trip test for catching a scaling change?
3. A sender's cycle time is 20 ms and the receiver's timeout is 15 ms. Which test finds this, and why is `time.sleep` unnecessary?
4. When an integration test fails, what should you do besides fixing the bug?

<!--ANSWERS-->
1. For instance: mismatched byte order or scaling between sender and receiver; incompatible alive-counter wrap; inconsistent timeouts; receiver ignoring a validity flag.
2. The round trip uses the *same* definition on both sides, so a consistent wrong change still round-trips. Fixed bytes taken from the written specification fail as soon as either side drifts.
3. An integration test with a fake clock that advances by the sender's cycle (20 ms) and checks the receiver still shows data — it fails because 20 ms > 15 ms. The clock is simulated, so no real waiting is needed.
4. Add a unit test (or lowest-level reproduction) for the defect so it is guarded where it is cheapest and most precise; keep the integration test as the system-level check.
