# Automotive primer: the domain you will test

You do not need to be a vehicle engineer to complete this course, but you do need a working vocabulary. Each section below introduces a domain concept exactly as the code in `src/autotest` models it.

## 3.1 ECUs and in-vehicle networks

A vehicle is a network of **electronic control units (ECUs)** — small computers dedicated to engine, brakes, battery, instrument cluster, and so on. They exchange *signals* (vehicle speed, battery temperature, pedal position) over **buses**. The workhorse is the **CAN bus** (Controller Area Network).

### CAN in five facts
1. A **frame** carries an **arbitration identifier** (11 bits in standard frames, 29 in extended) and up to **8 data bytes** (classic CAN; CAN FD allows 64).
2. The identifier is *not* an address — it names the **message** and sets its **priority**: when two nodes transmit simultaneously, the lower identifier wins arbitration without data loss.
3. Any node can listen to any frame; receivers *filter* by identifier.
4. Typical speed is 500 kbit/s. A full 8-byte frame is 111 bit-times including intermission before bit stuffing, so a saturated bus carries roughly 4 500 frames/s at most (fewer after stuffing). Lab 10 uses this number as a throughput budget.
5. Hardware checks a 15-bit CRC, but *application-level* protection (below) is still needed for safety-critical signals.

```python
# verified: python
from autotest.can import CANFrame

frame = CANFrame(arbitration_id=0x1A0, data=bytes([0x10, 0x27, 0x01]))
print(f"id=0x{frame.arbitration_id:03X} dlc={frame.dlc} data={frame.data.hex(' ')}")
try:
    CANFrame(0x800)            # 12 bits do not fit a standard identifier
except ValueError as e:
    print("rejected:", e)
```

### Signals: physical values packed into bits
Engineers do not send "100.0 km/h"; they send an integer **raw value** in a bit field and agree a **scaling**:

```
physical = raw × factor + offset
```

A message definition lists each signal's *start bit*, *length*, *factor* and *offset* (in practice in a "DBC" file). Example from the wheel-speed message: a 16-bit raw value with factor 0.01 represents 0.00…655.35 km/h with 0.01 km/h resolution — and quantisation means a round trip is accurate only *to within one step* (the point of Lab 7's round-trip property).

```python
# verified: python
from autotest.can import Signal

speed = Signal("speed_kmh", start_bit=0, length=16, factor=0.01, minimum=0, maximum=300)
raw = speed.to_raw(100.0)
print(raw, speed.to_physical(raw))     # 10000 100.0
print(speed.to_raw(0.004))             # 0  -> resolution is 0.01
```

### End-to-end (E2E) protection
Safety-related signals travel with extra protection so a receiver can detect corruption, loss, repetition, or a stuck sender. Our model uses the common pattern from AUTOSAR E2E:

| Mechanism | Detects | In `autotest.can` |
|---|---|---|
| **CRC-8** (SAE J1850 polynomial 0x1D) | corrupted bits | `crc8`, first byte |
| **Alive counter** (4 bit, wraps 15 → 0) | lost, repeated or stale frames | second byte |
| **Timeout** | sender silent | cluster blanks after 100 ms |

On any failure the receiver must not use the data and typically falls back to a safe value (the cluster shows `--`) and records a diagnostic code.

## 3.2 Diagnostics: DTCs and UDS

When an ECU detects a fault it stores a **diagnostic trouble code (DTC)**, e.g. `U0121` (lost communication with the ABS module; the letter gives the domain: **P**owertrain, **C**hassis, **B**ody, **U** (network / communication)). To avoid false alarms, a fault must usually persist for several monitoring cycles before the DTC is *confirmed* — **debouncing**. After enough healthy cycles the DTC stops being *active* but stays *stored* as history until a technician clears it.

A workshop tester talks to the ECU using **UDS** (Unified Diagnostic Services, ISO 14229). Requests start with a service id; a **positive response** adds `0x40` to it; a **negative response** is `0x7F <service> <code>`:

| Service | Request | Positive | Our `DiagnosticManager` |
|---|---|---|---|
| ReadDTCInformation | `19 02 <mask>` | `59 02 …` | stored DTCs |
| ClearDiagnosticInformation | `14 …` | `54` | clears history |
| ReadDataByIdentifier | `22 F1 90` | `62 F1 90 <VIN>` | reads the VIN |
| anything else | — | `7F <svc> 11` | *service not supported* |

Because the diagnostic port is reachable by anyone with an OBD dongle, its parser is a classic target for **robustness testing and fuzzing** (Lab 8).

## 3.3 Battery management (BMS)

An electric vehicle's traction battery is built from many **cells** (typically 3.0–4.2 V each for lithium-ion). The **battery management system** protects and monitors them:

* **State of charge (SOC)** — percent of capacity remaining. **Coulomb counting** integrates current: `ΔSOC = I · Δt / capacity`. Charging current is positive.
* **Cell protection** — a cell above ~4.2 V (over-voltage) or below ~3.0 V (under-voltage), or the pack outside a safe temperature, must raise a fault.
* **Charge derating** — allowed charge current depends on temperature and SOC: no charging below 0 °C (lithium plating) or above 45 °C, reduced current when cold, and a taper to zero between 80 % and 100 % SOC. This is the decision table you will design tests for in Lab 3.

## 3.4 Cruise control

The cruise controller is a **mode state machine** plus a **control law**:

```
 OFF ──power_on──► STANDBY ──set(v)──► ACTIVE ◄──accelerator released── OVERRIDE
                      ▲                  │  └──────accelerator pressed───────►┘
                      └─ brake / cancel ─┘
```

The control law is a **PI controller** (proportional–integral): throttle = Kp·error + Ki·∫error. The proportional term reacts to the present error; the integral term removes the steady-state error (e.g. on a hill). A real implementation needs **anti-windup** — stop integrating while the actuator is saturated — or the controller overshoots badly after a long saturation. Closed-loop quality is expressed with measures such as **overshoot**, **settling time** and **steady-state error** (Lab 11).

## 3.5 Anti-lock braking (ABS)

When a wheel brakes harder than the tyre can grip it locks, and a locked wheel cannot steer. Tyre force depends on **slip ratio**:

```
slip = (vehicle_speed − wheel_speed) / vehicle_speed        0 = free rolling, 1 = locked
```

Friction rises with slip up to a **peak at roughly 10–30 % slip** and falls off toward lock-up (our simplified model peaks at 20 %). ABS rapidly **applies, holds and releases** brake pressure to keep slip near the peak — shortest stopping distance *and* steering ability. Below a minimum speed ABS stays out of the way.

## 3.6 Tyre pressure monitoring (TPMS)

Tyre pressure rises with temperature (constant volume: `p/T` is constant, with `T` in kelvin). To compare readings fairly the system **normalises to 20 °C**: `p20 = p · 293.15 / (273.15 + T)`. Thresholds relative to nominal pressure define OK / LOW / CRITICAL / HIGH, and a rapid drop within a window signals a leak. This is the capstone's system under test.

## 3.7 Functional safety in one page: ISO 26262

**ISO 26262** is the functional-safety standard for road vehicles. The ideas that matter for testers:

* **Hazard analysis and risk assessment** rates each hazardous event by *severity*, *exposure* and *controllability*, producing an **ASIL** — *Automotive Safety Integrity Level* — from **A** (lowest) to **D** (highest), or *QM* (quality management only).
* The **higher the ASIL, the more rigorous the required verification**: more methods, stricter coverage metrics, more independence.
* **Part 6** covers product development at the *software level*: unit design and implementation, **unit verification**, **integration and verification**, and testing of the embedded software. The methods it names — requirements-based tests, **interface tests**, **fault-injection tests**, **resource-usage evaluation**, **equivalence classes**, **boundary values**, **error guessing**, **structural coverage** (statement, branch, MC/DC) and back-to-back comparison — are precisely the techniques of Labs 3–13.
* Evidence matters: the safety case needs **traceability** from safety requirement to test to result (Lab 13).

A related process standard, **Automotive SPICE**, expects the same discipline in its software verification processes (unit verification, component/integration verification, software qualification test).

> **This course teaches the techniques these standards ask for. It is not a compliance course** — consult the edition of the standard your organisation follows, and your safety manager, for obligations on a real programme.

## Check your understanding

1. Why does a CAN receiver need an alive counter *in addition to* a CRC?
2. A signal has factor 0.25, offset −40, and raw value 130. What is the physical value? What is the smallest change in physical value the signal can represent?
3. In a DTC with `fail_threshold=3`, a monitor reports fail, fail, pass, fail, fail. Is the code confirmed? Why does debouncing exist?
4. Why does the slip curve make "brake as hard as possible" a poor strategy on a real road?

<!--ANSWERS-->
1. A CRC only proves the *bits* are intact. A frame that is perfectly valid but old — repeated by a stuck sender, replayed, or arriving after intermediate frames were lost — still passes the CRC. The counter shows whether the sequence is continuous.
2. 130 × 0.25 − 40 = −7.5. Resolution is the factor: 0.25.
3. No: the failures were never three *consecutive* ones (the pass in the middle resets the streak). Debouncing avoids storing codes for transient glitches such as a single noisy sample.
4. Beyond the peak slip, friction *falls*: the locked wheel decelerates the car less and cannot steer. ABS deliberately releases pressure to stay near the peak.
