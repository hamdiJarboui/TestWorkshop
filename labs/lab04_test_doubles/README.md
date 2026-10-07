# Lab 4 — Test doubles: isolating the unit

> **Read first:** Chapter 7 — *Isolating the unit: testability and test doubles* (`course/lecture_07_test_doubles.md`).

**Duration:** 2.5 h · **Type:** isolation techniques · **Code under test:** `TemperatureSensor`, `InstrumentCluster`, `WheelSpeedECU`

## Why it matters
Real ECU software talks to ADCs, buses, NVM and other ECUs. On a CI server none of those exist, and some situations
(short-to-ground, 100 ms bus silence) cannot be produced safely or repeatably on hardware. Doubles make the world scriptable.

## The five doubles (Meszaros)
| Double | Role | Example here |
|---|---|---|
| **Dummy** | placeholder | a listener on an id that never fires |
| **Stub** | canned answers | `StubADC(0)` |
| **Fake** | simplified real implementation | `SineWaveADC`, `FakeClock`, `VirtualCANBus` |
| **Spy** | records usage | `SpyADC.calls` |
| **Mock** | verifies expected interactions | `Mock(spec=DiagnosticManager)` |

## Key skills
* `mock.Mock(spec=Class)` — typos in method names raise instead of silently passing.
* `side_effect=[...]` for sequences and exceptions; `call_count`, `assert_called_with`.
* **Patch where the name is looked up** (`autotest.ecu.e2e_protect`, not `autotest.can.e2e_protect`).
* **Inject time:** `FakeClock.advance(0.5)` replaces `time.sleep(0.5)` — fast and deterministic.

## Run it
`pytest labs/lab04_test_doubles -v`

## Exercises — `exercise_lab04.py`
Spy on the alive counter · simulate an `OSError` from the ADC · timeout boundary at 99/101 ms with a fake clock · write 3 sentences on when a mock-based test is *bad*.

## Debrief
* The last worked test prefers the **real** `DiagnosticManager` over a mock. Why? What does the mock version lock in?
* What would break if `ecu.py` did `from .can import e2e_protect` and you patched `autotest.can.e2e_protect`?
* Which doubles would you need to test a *real* `BenchADC` driver?
