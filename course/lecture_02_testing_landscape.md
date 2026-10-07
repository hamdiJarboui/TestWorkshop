# The testing landscape

Testing is not one activity but a family of them. This chapter gives you the map so that every later lab has a place on it.

## 2.1 Test levels: the V-model

The classic way to organise software verification is the **V-model**. The left arm refines requirements into design and code; the right arm verifies each left-hand artefact with a matching test level.

```
 Requirements ─────────────────────────────────────────────► Acceptance / vehicle tests
     │                                                                ▲
     ▼                                                                │
 System design ──────────────────────────────────────► System integration & tests
     │                                                          ▲
     ▼                                                          │
 Software architecture ─────────────────────► Software integration tests
     │                                                  ▲
     ▼                                                  │
 Unit design ────────────────────► Unit tests
     │                                   ▲
     └────────────► Implementation ──────┘
```

| Level | Question | Typical object | Course labs |
|---|---|---|---|
| **Unit** | Does this function/class do what its design says? | `crc8`, `max_charge_current` | 1, 2, 3, 7 |
| **Integration** | Do these components agree on their interfaces? | ECU ↔ bus ↔ cluster | 4, 5, 8 |
| **System** | Does the assembled system meet its requirements? | cruise control behaviour | 6, 9, 10, 11 |
| **Acceptance** | Is it fit for purpose for the stakeholder? | requirement scenarios | 13 |

The V-model is a *map*, not a waterfall mandate; agile teams run all levels continuously, but the questions stay the same.

## 2.2 Test types: what you check

Orthogonal to *level* is the *type* — the quality attribute under test:

| Type | Checks | Example here |
|---|---|---|
| **Functional** | Correct results | charge-current table (Lab 3) |
| **Non-functional** | Time, memory, robustness, security | 10 ms control cycle (Lab 10), fuzzed diagnostics (Lab 8) |
| **Structural (white box)** | Internal paths were exercised | branch coverage (Lab 12) |
| **Change-related** | Nothing broke | regression, golden files (Lab 9) |
| **Back-to-back** | Two implementations agree | model vs. code (Lab 11 mindset) |

### Black box, white box, grey box
* **Black-box** (specification-based): tests derive from the *requirements*, ignoring the code. They survive refactoring. Techniques: equivalence classes, boundary values, decision tables (Chapter 6).
* **White-box** (structure-based): tests derive from *code structure* — statements, branches, conditions. They measure completeness. (Chapter 15.)
* **Grey-box**: mostly black-box, but using knowledge of internals to craft inputs (e.g. knowing the alive counter wraps at 16).

Good practice combines them: design black-box from the spec, then use white-box *coverage* to find what you forgot.

## 2.3 Static and dynamic verification

**Static** techniques analyse without running: code review, linting, type checking, formal analysis. **Dynamic** techniques *execute* the software — that is testing proper. They complement each other; this book is dynamic testing, but a real pipeline also runs `ruff`/`mypy`/MISRA-style checkers.

## 2.4 X-in-the-loop: where the code runs

Embedded software is tested in progressively more realistic environments. The *same* test logic is reused as the environment changes:

| Stage | Software | Plant (vehicle/hardware) | Used for |
|---|---|---|---|
| **MIL** model-in-the-loop | Simulink/Python *model* | simulated | early algorithm design |
| **SIL** software-in-the-loop | production *source code* on a PC | simulated | **Labs 11–13**: fast, repeatable, CI-friendly |
| **PIL** processor-in-the-loop | compiled code on target CPU | simulated | numeric / timing effects of the real compiler and CPU |
| **HIL** hardware-in-the-loop | real ECU | real-time simulator + fault insertion | final ECU verification, safe fault injection |
| **VIL / vehicle** | real ECU | real car or proving ground | validation |

Each step is slower, costlier and less reproducible — but closer to reality. A practical strategy pushes as many checks as possible *left* (cheap, early) and reserves the right for what only reality can show. Lab 13 demonstrates the technique that makes this work: **one test body, interchangeable back-ends**.

## 2.5 The test pyramid

Because cost and fragility grow with the scope of a test, healthy suites are shaped like a pyramid:

```
                   ▲   few        slow, expensive, broad       vehicle / HIL
                  ╱ ╲
                 ╱   ╲            system / closed-loop (SIL)
                ╱─────╲
               ╱       ╲          integration (bus, interfaces)
              ╱─────────╲
             ╱           ╲        many   fast, cheap, precise   unit tests
            ╱─────────────╲
```

* **Many unit tests** — milliseconds each, pinpoint the failing function.
* **Fewer integration tests** — seconds, verify interfaces.
* **Few system/HIL tests** — minutes to hours, verify end-to-end behaviour.

The anti-pattern is the **ice-cream cone**: a few unit tests and a mountain of slow manual or end-to-end tests. Failures are then hard to localise, runs are slow, and people stop running them.

## 2.6 Properties of a good test: F.I.R.S.T.

| Letter | Property | In practice |
|---|---|---|
| **F**ast | Milliseconds | no `sleep`, no network, simulated hardware |
| **I**ndependent | Any order, alone | fresh fixtures, no shared mutable state |
| **R**epeatable | Same result every run | inject clocks, seed random generators |
| **S**elf-validating | Pass/fail without reading logs | assertions, not `print` |
| **T**imely | Written with (or before) the code | bug → failing test → fix |

## 2.7 Anatomy: Arrange – Act – Assert

Nearly every test, in any framework, has the same three phases (also written *Given – When – Then*):

```python
# verified: python
from autotest.bms import max_charge_current

def test_charge_current_tapers_at_90_percent():
    # Arrange: a pack at 90 % SOC and 25 °C (here: just the inputs)
    soc, temp = 90, 25
    # Act: call the unit under test once
    current = max_charge_current(soc, temp)
    # Assert: compare with the value the SPECIFICATION gives (not the code's output!)
    assert current == 50.0

test_charge_current_tapers_at_90_percent()
print("ok")
```

Two habits follow: **one reason to fail per test** (so the name tells you what broke), and **derive the expected value from the specification**, never by running the code and pasting its output — that would merely freeze whatever bug exists.

## 2.8 Choosing a test strategy

A test *strategy* answers: *what will we test, at which level, with which technique, how will we know it is enough, and how often will we run it?* A compact decision guide:

| Risk / situation | Reach for |
|---|---|
| Pure calculation with clear rules | unit tests + boundary values (Labs 2–3) |
| Logic with modes and history | state-transition tests (Lab 6) |
| Code that talks to hardware or other ECUs | test doubles, then integration tests (Labs 4–5) |
| Parsers, codecs, anything with big input spaces | property-based + fuzz (Labs 7–8) |
| Behaviour under failure | fault injection (Lab 8) |
| "It worked last release" | regression suite + golden logs (Lab 9) |
| Real-time or resource limits | budget tests (Lab 10) |
| Control loops | simulation with acceptance criteria (Lab 11) |
| "Are the tests any good?" | coverage + mutation (Lab 12) |
| Audit / safety case | traceability (Lab 13) |

## Check your understanding

1. Place each on the V-model: (a) checking that CRC-8 of `"123456789"` is `0x4B`; (b) checking that the cluster shows `--` after 100 ms of bus silence; (c) braking from 100 km/h in a simulation and measuring distance.
2. Why is a suite with 5 unit tests and 200 end-to-end UI tests considered unhealthy?
3. What is the difference between SIL and HIL, and why would you still run SIL tests when HIL exists?
4. The assertion `assert max_charge_current(90, 25) == max_charge_current(90, 25)` always passes. Which F.I.R.S.T. or oracle principle does it violate?

<!--ANSWERS-->
1. (a) Unit; (b) integration (two ECUs and a bus, with timing); (c) system-level closed-loop (SIL).
2. It is an "ice-cream cone": slow, brittle, hard to localise failures, expensive to run, so it is run rarely and trusted little. A broad base of fast unit tests should carry most of the weight.
3. SIL runs the production code on a PC against a simulated plant; HIL runs the real ECU against a real-time simulator. SIL is far faster, cheaper, parallelisable and available before hardware exists; it catches most logic defects early, leaving HIL for hardware/timing effects.
4. It has no independent oracle — both sides come from the code, so no bug can make it fail. The expected value must come from the specification (`50.0`).
