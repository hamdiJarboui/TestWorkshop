# Lab 5 — Integration testing

**Duration:** 3 h · **Type:** integration / interface / contract testing · **Code under test:** `WheelSpeedECU → VirtualCANBus → InstrumentCluster`

## Why it matters
Most field failures sit *between* components: one team scales by 0.01, another by 0.1; the alive counter wraps and the
receiver rejects it; a CRC covers the wrong bytes. Unit tests of each side pass; the system is wrong.

## Learning objectives
Test an interface end-to-end through a virtual bus; inject faults (corruption, loss, noise) with bus hooks; verify E2E
protection and timeouts; write a **contract test** against the exact bytes on the wire; recognise smoke tests.

## Strategy: integration order
*Bottom-up* (codec → ECU → bus → cluster) was used to build the SUT; *top-down* with stubs is the alternative. Choose by risk —
integrate the riskiest interface first.

## Run it
```bash
pytest labs/lab05_integration -v
pytest labs/lab05_integration -m smoke        # a single, fastest end-to-end check
```

## Guided tour
* `test_speed_travels_from_sensor_ecu_to_display` — the **smoke** test.
* `test_frame_on_the_wire_matches_the_interface_specification` — byte-level contract.
* `test_cluster_blanks_after_100ms...` — timing via `FakeClock`, both sides of 100 ms.
* `test_corrupted_frame...`, `test_lost_frame...` — `bus.add_fault(hook)`; a hook returns a modified frame or `None`.

> **Real finding:** writing the Lab 9 replay later exposed that one corrupted frame cost *two* frames (BUG-130).
> Integration tests are where such cross-component sequencing defects hide.

## Exercises — `exercise_lab05.py`
Add a third node (data logger) · seeded random bit-flips on 1 in 5 frames · a contract test that fails if the scale factor changes.

## Debrief
* What does a contract test protect that a round-trip test cannot?
* Why must the fault-injection RNG be seeded?
* Which failures can only be found at integration level? Which would you rather find at unit level?
