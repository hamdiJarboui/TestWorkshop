# Glossary

| Term | Meaning |
|---|---|
| **Acceptance test** | Test deciding whether a system satisfies stakeholder needs; often written as Given/When/Then scenarios. |
| **Alive counter** | A small counter incremented with every message so receivers can detect lost, repeated or stale frames. |
| **Anti-windup** | Control-law technique that stops the integral term accumulating while the actuator is saturated. |
| **Arrange–Act–Assert (AAA)** | The three phases of a test: set up, perform the action, check the result. (Given–When–Then.) |
| **ASIL** | Automotive Safety Integrity Level (A–D, plus QM): ISO 26262's measure of required rigour. |
| **Assertion** | A statement in a test that must hold; failure signals a defect. |
| **Back-to-back test** | Comparing two implementations (e.g. model and generated code) on the same inputs. |
| **BDD** | Behaviour-driven development: specifying behaviour as readable scenarios that double as tests. |
| **BMS** | Battery management system: monitors and protects a battery pack. |
| **Boundary value analysis** | Test design that checks values on and either side of class boundaries. |
| **Branch coverage** | Fraction of decision outcomes (true/false) exercised by the tests. |
| **CAN** | Controller Area Network: the standard in-vehicle serial bus. |
| **CI** | Continuous integration: automatically building and testing every change. |
| **Contract test** | Test pinning an interface's exact behaviour (e.g. the bytes on the wire). |
| **Coverage** | A measure of how much code (or how many requirements) the tests exercised. |
| **CRC** | Cyclic redundancy check: a checksum detecting corrupted data. |
| **Decision table** | Table of condition combinations and the resulting action. |
| **DBC / ARXML** | Formats describing CAN messages and signals (layout, scaling). |
| **Dependency injection** | Passing a component's collaborators in from outside instead of creating them inside. |
| **DTC** | Diagnostic trouble code: stored identifier of a detected fault. |
| **Debouncing** | Requiring a condition to persist (N cycles) before acting on it. |
| **E2E protection** | End-to-end protection of safety-relevant data (CRC + counter + timeout). |
| **ECU** | Electronic control unit: an embedded computer in a vehicle. |
| **Equivalence class** | Set of inputs the specification treats identically. |
| **Equivalent mutant** | A mutant whose behaviour is identical to the original; cannot be killed by any test. |
| **Error / fault / failure** | Human mistake / the defect it leaves in the code / the wrong behaviour observed at run time. |
| **Fail-safe / fail-operational** | Reaction that moves to a harmless state / that keeps degraded service. |
| **Fake** | A simplified working implementation used in tests (e.g. in-memory bus). |
| **Fault injection** | Deliberately introducing faults to verify detection and reaction. |
| **Fixture** | Prepared environment or object a test needs. |
| **Flaky test** | A test with non-deterministic outcome without code change. |
| **FMI** | Functional Mock-up Interface: standard for exchanging simulation models. |
| **Fuzzing** | Feeding random/malformed inputs to find crashes and vulnerabilities. |
| **Golden file** | Stored, approved output that new output is compared against. |
| **Hardware-in-the-loop (HIL)** | Testing a real ECU against a real-time simulation of its environment. |
| **Hypothesis** | Python library for property-based testing. |
| **Integration test** | Test of several components working together and their interfaces. |
| **Invariant** | A condition that must hold in every reachable state. |
| **ISO 26262** | Functional safety standard for road vehicles. |
| **Jitter** | Variation in timing of a periodic event. |
| **MC/DC** | Modified condition/decision coverage: each condition shown to independently affect the outcome. |
| **Metamorphic testing** | Testing a relation between outputs of related inputs when no exact oracle exists. |
| **MIL / SIL / PIL** | Model- / software- / processor-in-the-loop. |
| **Mock** | A test double that verifies interactions (calls) against expectations. |
| **Mutation score** | Fraction of mutants killed by a test suite. |
| **Oracle** | The mechanism deciding whether an observed result is correct. |
| **Overshoot** | How far a controlled quantity exceeds its target during a step response. |
| **Parametrization** | Running one test body with several data sets. |
| **PI controller** | Controller with proportional and integral terms. |
| **Plant** | The controlled system (vehicle, tyre, battery) in a control-loop simulation. |
| **Property-based test** | Test asserting a statement for all generated inputs. |
| **pytest** | Third-party Python test framework; de-facto standard. |
| **Regression** | Previously working behaviour that breaks after a change. |
| **Replay** | Feeding recorded traces into the system under test. |
| **Seam** | A point where behaviour can be substituted without editing the code. |
| **Shrinking** | Simplifying a failing input to a minimal counter-example. |
| **Slip ratio** | (vehicle speed − wheel speed) / vehicle speed; 0 free rolling, 1 locked. |
| **Smoke test** | Minimal check that the system is basically alive. |
| **SOC** | State of charge of a battery. |
| **Spy** | A test double that records how it was used. |
| **State-transition testing** | Test design from a state machine: states, events, transitions. |
| **Stub** | A test double returning canned answers. |
| **SUT / CUT** | System / component under test. |
| **Test double** | Any stand-in for a real collaborator (dummy, stub, fake, spy, mock). |
| **Test pyramid** | Many fast unit tests, fewer integration tests, few slow system tests. |
| **TPMS** | Tyre pressure monitoring system. |
| **UDS** | Unified Diagnostic Services (ISO 14229): the diagnostic protocol of ECUs. |
| **unittest** | Python's built-in xUnit-style test framework. |
| **V-model** | Process model pairing each development level with a verification level. |
| **Validation / verification** | Building the right product / building the product right. |
| **WCET** | Worst-case execution time of a task. |
| **xfail** | A test expected to fail (known bug), tracked until fixed. |
