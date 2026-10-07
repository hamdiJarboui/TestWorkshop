# State-based and system-level testing

## 9.1 Behaviour that depends on history

Some behaviour cannot be understood from the *current input* alone. The cruise controller reacts to "brake pressed" differently depending on whether it is OFF, STANDBY, ACTIVE or OVERRIDE. Such systems are described by **state machines**: a set of **states**, **events** (inputs), **transitions** (state × event → next state, possibly with an action), and an initial state.

```
                  power_on                 set(v) [30..180]
        OFF ───────────────► STANDBY ─────────────────────► ACTIVE
         ▲                    ▲  ▲                          │ ▲  │
         │                    │  └── brake / cancel ────────┘ │  │ accelerator pressed
         │                    │                               │  ▼
         │                    └──── brake / cancel ─────── OVERRIDE
         └──────────────── power_off (from any state) ────────┘
```

State-based defects are typical safety hazards: *"cruise stays active after braking"*, *"re-engages unexpectedly"*, *"throttle non-zero in STANDBY"*.

## 9.2 From diagram to transition table

A diagram shows the *valid* arrows; a **state-transition table** also shows what happens for **every** event in every state, including events that should be *ignored*. This completeness is what finds missing handling:

| state \ event | power_on | power_off | set | resume | cancel | accel_on | accel_off |
|---|---|---|---|---|---|---|---|
| OFF | STANDBY | OFF | OFF (refused) | OFF | OFF | OFF | OFF |
| STANDBY | STANDBY | OFF | ACTIVE | STANDBY¹ | STANDBY | STANDBY | STANDBY |
| ACTIVE | ACTIVE | OFF | ACTIVE | ACTIVE | STANDBY | OVERRIDE | ACTIVE |
| OVERRIDE | OVERRIDE | OFF | ACTIVE | OVERRIDE | STANDBY | OVERRIDE | ACTIVE |

¹ `resume` from STANDBY becomes ACTIVE only if a saved target exists and the speed is ≥ 30 km/h.

This 4 × 7 table is a complete test specification: 28 rows → 28 tests, and *every* cell is a decision someone made — or forgot to make.

## 9.3 Coverage levels for state machines

| Level | Requirement | Strength |
|---|---|---|
| **All-states** | visit every state | weakest |
| **All-transitions (0-switch)** | take every *valid* transition once | the usual minimum |
| **All invalid events** | every event in every state, including "should be ignored" | finds missing handling |
| **n-switch** | every *sequence* of *n+1* consecutive transitions | finds history-dependent faults |
| **Exhaustive sequences up to length n** | all event sequences of length *n* | strongest, grows as *eⁿ* |

For 7 events, all sequences of length 3 number 7³ = 343 — still trivial for a computer, impossible by hand. That is the power of generating them.

## 9.3.1 Testing a table in code

```python
# verified: pytest
import pytest
from autotest.cruise import CruiseController, CruiseState as S

def drive_into(state):
    cc = CruiseController()
    if state in ("standby", "active", "override"):
        cc.power_on()
    if state in ("active", "override"):
        cc.set(100)
    if state == "override":
        cc.accelerator(True)
    return cc

EVENTS = {"power_on": lambda c: c.power_on(), "power_off": lambda c: c.power_off(),
          "set": lambda c: c.set(100), "cancel": lambda c: c.cancel(),
          "accel_on": lambda c: c.accelerator(True), "accel_off": lambda c: c.accelerator(False)}

@pytest.mark.parametrize("state, event, expected", [
    ("off", "power_on", S.STANDBY), ("off", "set", S.OFF),
    ("standby", "set", S.ACTIVE), ("standby", "accel_on", S.STANDBY),
    ("active", "cancel", S.STANDBY), ("active", "accel_on", S.OVERRIDE),
    ("override", "accel_off", S.ACTIVE), ("override", "power_off", S.OFF),
])
def test_transitions(state, event, expected):
    cc = drive_into(state)
    EVENTS[event](cc)
    assert cc.state is expected
```

## 9.4 Invariants over exhaustive sequences

Writing the expected *next state* for 343 sequences is pointless; instead assert **invariants** — facts that must hold in *every* reachable state:

* throttle is exactly 0 unless the state is ACTIVE;
* the controller has a target if and only if it is ACTIVE (or OVERRIDE, where the target is remembered);
* nothing ever raises an exception.

```python
# verified: python
import itertools
from autotest.cruise import CruiseController, CruiseState as S

EVENTS = {
    "power_on": lambda c: c.power_on(), "power_off": lambda c: c.power_off(),
    "set": lambda c: c.set(100), "resume": lambda c: c.resume(100), "cancel": lambda c: c.cancel(),
    "accel_on": lambda c: c.accelerator(True), "accel_off": lambda c: c.accelerator(False),
}

checked = 0
for sequence in itertools.product(EVENTS, repeat=3):
    cc = CruiseController()
    for name in sequence:
        EVENTS[name](cc)
        assert (cc.state is S.ACTIVE) == (cc.target is not None) or cc.state is S.OVERRIDE
        if cc.state is not S.ACTIVE:
            assert cc.control(50, 0.1) == 0.0          # SAFETY: no throttle outside ACTIVE
    checked += 1
print(f"{checked} sequences keep every invariant")
```

This is a **model-free oracle**: we do not need to know the exact state after each sequence, only that the *rules of the system* are never violated.

## 9.5 Testing the control law

The cruise controller is also a numerical algorithm. Verify it at two levels:

1. **Unit level:** exact values from a hand calculation. With Kp = 0.05, Ki = 0.01, target 100, speed 90, dt = 0.1: `u₁ = 0.05·10 + 0.01·(0 + 10·0.1) = 0.51`. Then `0.52`, `0.53`.
2. **Property level:** output is always within [0, 1] (saturation), and **anti-windup** holds — while the output is saturated the integral must not keep growing.

```python
# verified: pytest
import pytest
from autotest.cruise import CruiseController

def test_pi_law_matches_hand_calculation():
    cc = CruiseController(kp=0.05, ki=0.01)
    cc.power_on(); cc.set(100)
    assert [cc.control(90, 0.1) for _ in range(3)] == pytest.approx([0.51, 0.52, 0.53])

def test_no_integral_windup_while_saturated():
    cc = CruiseController()
    cc.power_on(); cc.set(100)
    for _ in range(1000):
        assert cc.control(30, 0.1) == 1.0          # far below target: saturated at full throttle
    assert cc._integral == 0.0                      # white-box: the integral did not wind up
```

The second test peeks at private state — a deliberate **white-box** check, acceptable here because the *behavioural* consequence of windup (huge overshoot later) would be slow and indirect to demonstrate. Closed-loop effects belong to Chapter 14.

## 9.6 System tests: scenarios

A **system test** exercises the assembled behaviour against *requirements*. A good format is a **scenario** in *Given / When / Then* form:

```
Scenario: Driver overtakes while cruising
  Given cruise control is ACTIVE at 100 km/h
  When  the driver presses the accelerator for 5 s and then releases it
  Then  cruise control is ACTIVE again with the SAME target of 100 km/h
   And  the throttle request after release stays below 0.5
```

Each clause maps to code: *Given* = fixture, *When* = stimulus, *Then* = assertions. Writing scenarios in customer language makes them reviewable by requirement owners and test engineers who do not read Python.

## 9.7 Oracles for system tests

Because the full system has no single "expected value", system tests lean on:

* **Requirement oracles** — concrete limits (`dip < 4 km/h`).
* **Invariants / safety properties** — "never", "always".
* **Reference models** — a simple simulation or earlier release to compare against (**back-to-back testing**).
* **Metamorphic relations** — e.g. a higher target never produces a lower steady-state speed.

## 9.8 Practical advice

* **Draw the diagram first**; if you cannot, the behaviour is under-specified.
* Test **invalid events** — they are where state machines misbehave.
* Keep the *model* (table) next to the tests; when the design changes, change the table first.
* If states explode, partition into **hierarchical** machines or restrict exhaustive testing to the safety-relevant subset.

## Check your understanding

1. State machine with 5 states and 6 events: how many cells has the complete transition table, and what does covering only the valid arrows miss?
2. Why assert invariants over all 3-event sequences instead of explicit expected states?
3. Write the *Then* clause for: "Given cruise ACTIVE, When the driver presses the brake".
4. What is anti-windup and which symptom reveals its absence in a closed-loop test?

<!--ANSWERS-->
1. 5 × 6 = 30 cells. Covering only valid arrows misses events that should be *ignored or refused* in states where they are meaningless, which is where unintended behaviour hides.
2. 343+ sequences make hand-written expected states impractical and error-prone; invariants (e.g. "no throttle outside ACTIVE") are short, always true, and detect hazards in every reachable state.
3. "Then cruise control is STANDBY, the target is cleared, the saved target keeps the previous set speed, and the throttle request is 0."
4. Anti-windup stops the integral term accumulating while the actuator is saturated. Without it the controller overshoots badly and takes long to settle after a long saturation (e.g. after a hill or a big set-speed step).
