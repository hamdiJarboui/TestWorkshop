# Why we test: foundations

## 1.1 What a test is — and what it is not

A **test** is an *experiment* on software: you set up a situation, provoke a behaviour, and compare what happened with what the specification says *should* happen. The comparison rule is called the **test oracle**. Everything in this course is a variation on that sentence:

```
   precondition                stimulus               observation
 ┌─────────────────────┐   ┌────────────────┐   ┌───────────────────────┐
 │ battery at 90 % SOC,│ → │ ask for charge │ → │ allowed current = 50 A│
 │ pack at 25 °C       │   │ current        │   │                       │
 └─────────────────────┘   └────────────────┘   └───────────┬───────────┘
                                                            ▼
                               oracle: "the spec says 50 A" ──► PASS
```

Three things distinguish a good test from a script that merely calls the code:

1. **It is automated and repeatable** — anyone, any day, gets the same verdict.
2. **It has an oracle** — it *decides* pass or fail; a human does not need to read a log.
3. **It is independent** of other tests — it can run alone, in any order.

Testing is **not** debugging. Testing *finds* a failure; debugging *locates and removes* its cause. Testing is **not** quality assurance either: QA is the whole process (requirements reviews, coding standards, audits, testing); testing is one activity inside it.

> Edsger Dijkstra's famous remark applies to every chapter of this book: *testing can show the presence of defects, never their absence.* A suite that passes tells you "none of these experiments revealed a problem" — nothing more. The rest of the course is about making those experiments as revealing as possible.

## 1.2 Error, fault, failure

Engineers use three words that everyday language blurs. Keeping them apart makes bug reports precise:

| Term | Meaning | Example from this course |
|---|---|---|
| **Error** (mistake) | A human slip | The programmer assumes every comparison with NaN behaves like a number |
| **Fault** (defect, bug) | The wrong code or data that results | `max_charge_current` compares `temp_c < 0 or temp_c > 45`, which is `False` for NaN |
| **Failure** | Observable wrong behaviour at run time | A sensor glitch reports NaN and the BMS allows **100 A** charging at an unknown temperature |

A fault is *latent* until an input activates it. Most test design is about choosing inputs that **activate** faults (boundaries, rare combinations, hostile values) and then **propagate** the wrong value to something the test can observe.

## 1.3 Verification and validation

* **Verification** — "Are we building the product *right*?" Checking against the specification: does the code do what requirement REQ-BMS-001 says?
* **Validation** — "Are we building the *right* product?" Checking against real needs: is that requirement what drivers and the safety case actually need?

Most automated tests in this book are *verification*. Acceptance scenarios (Lab 13) and closed-loop simulation (Lab 11) edge toward validation, because they ask whether the *behaviour* is acceptable, not only whether a function returns a number.

## 1.4 Why automotive software is different

A modern vehicle contains dozens of electronic control units (ECUs) running tens of millions of lines of code, supplied by many companies and integrated late. Several properties raise the bar for testing:

* **Safety.** A defect can injure people. Standards such as **ISO 26262** require a *systematic* verification argument with evidence — not just "we tested it."
* **Long life, many variants.** A platform lives for years and ships in hundreds of configurations. Re-testing by hand after every change is impossible; **regression automation** is the only option.
* **Distributed and real-time.** Behaviour emerges from ECUs talking over buses with deadlines of milliseconds. Many defects live *between* components.
* **Hardware coupling.** Software reads imperfect sensors, drives actuators and survives noisy power rails. Tests must model faults that rarely occur on a bench.
* **Cost of late defects.** A defect found by a unit test costs minutes; one found in the field can cost a software campaign or a recall. Finding defects *earlier* is the central economic argument for everything in this book.

## 1.5 The seven principles of testing

These principles, popularised by the ISTQB syllabus, summarise decades of experience. We return to each one in a lab.

1. **Testing shows the presence of defects, not their absence.** (Lab 12: a suite's *adequacy* must itself be measured.)
2. **Exhaustive testing is impossible.** `max_charge_current` has two continuous inputs; you cannot try them all. Hence *test design techniques* (Lab 3).
3. **Test early.** The unit tests of this course run in seconds, long before any hardware exists.
4. **Defects cluster.** A few modules — typically those with complex state or arithmetic at boundaries — contain most defects. Spend effort accordingly.
5. **The pesticide paradox.** Re-running the same tests finds fewer and fewer new defects. Vary and extend them (Labs 7, 8: generated and hostile inputs).
6. **Testing is context-dependent.** A BMS safety function and a radio menu deserve different rigour (ASIL levels, Chapter 3).
7. **Absence-of-errors fallacy.** Software that passes every test but implements the wrong requirement is still a failure (validation).

## 1.6 The vocabulary you will use daily

| Term | Meaning |
|---|---|
| **SUT / CUT** | System / component *under test* |
| **Test case** | Inputs + preconditions + expected result (+ postconditions) for one objective |
| **Test suite** | A collection of test cases run together |
| **Verdict** | Outcome of one test: *pass*, *fail* (oracle violated), *error* (test itself crashed), *skip*, *expected failure* |
| **Fixture** | The prepared environment a test needs (objects, files, simulated hardware) |
| **Test double** | A stand-in for a real collaborator (stub, fake, spy, mock) — Chapter 7 |
| **Coverage** | How much of the code (or requirements) the tests exercised — Chapter 15 |
| **Regression** | Previously working behaviour that breaks after a change |
| **Flaky test** | A test that sometimes passes and sometimes fails with no code change |
| **Smoke test** | A tiny, fast check that the system is basically alive |

## 1.7 How this course works

The book alternates **lecture chapters** (concepts, techniques, worked examples) with **labs** (runnable code and exercises). Every lab tests the *same* automotive library, `src/autotest`, so you spend your effort on technique rather than on learning new code:

```
CAN codec ─► sensors ─► BMS ─► cruise control ─► ABS ─► diagnostics
                                                            │
        ECUs on a virtual bus ─► tyre pressure (capstone) ◄─┘
```

You will use two frameworks: Python's built-in **`unittest`** (Chapter 4) and the community standard **`pytest`** (Chapter 5). Neither is "better" in every situation; you will learn both well enough to choose.

A tip that will serve you throughout: **read every test as a specification and every failing test as a question** — *which behaviour did I break, and was this test right to care?*

## Check your understanding

1. A temperature sensor driver returns `NaN` after a wiring fault, and a charging function lets 100 A flow. Name the error, the fault and the failure.
2. Is checking that `max_charge_current(50, 25) == 100.0` verification or validation? What question would turn it into validation?
3. Why is "we ran 10 000 tests and all passed" not evidence that the software is correct?
4. Give one reason automotive projects rely more heavily on automated regression tests than a typical web application.

<!--ANSWERS-->
1. *Error:* the developer assumed temperatures are always real numbers. *Fault:* comparisons with NaN are all false, so neither temperature limit triggers. *Failure:* full charge current is permitted at an unknown temperature.
2. Verification — it checks the code against a stated rule. Validation would ask whether "100 A at 25 °C and 50 % SOC" is actually what the cell supplier and safety case require, i.e. whether the rule itself is right.
3. Tests show presence, not absence, of defects. Ten thousand tests that all probe the same easy cases reveal nothing about boundaries, rare combinations or hostile inputs, and the suite itself may have weak assertions (Chapter 15).
4. Long-lived platforms with many variants, frequent software updates, and safety evidence that must be re-established after every change make manual re-testing economically and practically impossible.
