# Property-based testing and fuzzing

## 10.1 From examples to properties

An **example-based** test says: *for this input, expect that output.* Its weakness is obvious — it checks only the inputs **you thought of**. A **property-based** test says: *for **all** inputs of this kind, this statement is true*, and a tool generates hundreds of inputs to try to **falsify** it.

```
example test:    encode(100.0) == bytes 10 27
property test:   for every speed in [0, 300]:  decode(encode(speed)) ≈ speed
```

The tool we use is **Hypothesis**. Its three core ideas:

1. **Strategies** describe how to generate data (`st.integers()`, `st.floats(0, 300)`, `st.binary(max_size=8)`, `st.lists(...)`, `st.builds(Class, ...)`).
2. **Search**: it tries many inputs, biased toward troublemakers (0, −1, huge values, NaN, empty collections).
3. **Shrinking**: when it finds a failure it *simplifies* the input to the smallest counter-example it can, so the bug report is readable.

## 10.2 A first property: round trip

```python
# verified: pytest
import pytest
from hypothesis import given, strategies as st
from autotest.can import Signal

@given(st.floats(min_value=0, max_value=300, allow_nan=False))
def test_wheel_speed_round_trip_within_one_resolution_step(speed):
    sig = Signal("speed", 0, 16, factor=0.01, minimum=0, maximum=300)
    assert sig.to_physical(sig.to_raw(speed)) == pytest.approx(speed, abs=0.005 + 1e-9)
```

The tolerance is half the resolution (0.005): quantisation rounds to the nearest 0.01 step. Writing the property forced us to *state* that precision precisely — a specification question we might otherwise have skipped.

## 10.3 Shrinking in action

What if we (wrongly) claim the round trip is *exact*? Hypothesis finds a counter-example and shrinks it:

```python
# verified: python
from hypothesis import find, strategies as st
from autotest.can import Signal

sig = Signal("speed", 0, 16, factor=0.01)
smallest_bad = find(st.floats(min_value=0, max_value=300),
                    lambda x: sig.to_physical(sig.to_raw(x)) != x)
print("smallest counter-example found:", smallest_bad)
assert smallest_bad != sig.to_physical(sig.to_raw(smallest_bad))
```

Failures are also stored in a local example database (`.hypothesis/`), so a bug found once is **re-tested first** on every later run — automatic regression protection.

## 10.4 Finding good properties

"What property?" is the hard part. A catalogue of patterns, with automotive examples from this course:

| Pattern | Statement | Example |
|---|---|---|
| **Round trip** | `decode(encode(x)) ≈ x` | CAN signal codec; message with several signals |
| **Detection guarantee** | a corrupted input is always rejected | CRC detects *every* single-bit flip |
| **Invariant / safety** | something is true for all inputs | charge current is 0 outside 0–45 °C; always within [0, rated] |
| **Monotonicity** | more input → no more/less output | current never increases with SOC |
| **Idempotence** | doing it twice = once | `clear_all()` twice leaves the same state |
| **Reference model** | simple obviously-correct version agrees | a 10-line DTC debouncer vs the real manager |
| **Never crashes** | only documented errors occur | `CANFrame(...)` builds or raises `ValueError`, nothing else |
| **Metamorphic** | a known relation between runs | doubling the vehicle mass cannot shorten braking distance |

```python
# verified: pytest
from hypothesis import given, strategies as st
from autotest.bms import max_charge_current
from autotest.can import E2EStatus, e2e_check, e2e_protect

@given(st.binary(max_size=6), st.integers(0, 15), st.data())
def test_e2e_detects_any_single_bit_flip(payload, counter, data):
    protected = bytearray(e2e_protect(payload, counter))
    bit = data.draw(st.integers(0, len(protected) * 8 - 1))   # choose WHICH bit after seeing the length
    protected[bit // 8] ^= 1 << (bit % 8)
    status, _ = e2e_check(bytes(protected))
    assert status is not E2EStatus.OK

@given(st.floats(0, 100), st.floats(-60, 120))
def test_charge_current_is_always_within_limits_and_zero_when_outside_temperature_window(soc, temp):
    i = max_charge_current(soc, temp)
    assert 0.0 <= i <= 100.0
    if temp < 0 or temp > 45:
        assert i == 0.0                                       # safety property
```

A **safety property** like the second one is worth a great deal: it covers *every* SOC and temperature, including ones no engineer would think to try.

### A reference model

When the real code is intricate, write a **deliberately simple model** of the *specification* in the test and compare:

```python
# verified: pytest
from hypothesis import given, strategies as st
from autotest.diagnostics import DiagnosticManager

@given(st.lists(st.booleans(), max_size=40), st.integers(1, 4), st.integers(1, 4))
def test_dtc_matches_reference_model(history, fail_n, heal_n):
    fails = passes = 0
    active = stored = False
    for failed in history:                    # the SPEC in ten lines
        if failed:
            fails, passes = fails + 1, 0
            if fails >= fail_n:
                active = stored = True
        else:
            passes, fails = passes + 1, 0
            if passes >= heal_n:
                active = False
    mgr = DiagnosticManager(fail_threshold=fail_n, heal_threshold=heal_n)
    for failed in history:
        mgr.report("P0100", failed)
    assert (mgr.active_codes() == ["P0100"]) == (active and bool(history))
    assert (mgr.stored_codes() == ["P0100"]) == (stored and bool(history))
```

The model must come from the *requirement*, not from reading the code — otherwise you test the code against itself.

## 10.5 Steering the search

* `@settings(max_examples=500, deadline=None)` — more examples; disable the per-example time limit for slow code.
* `@example(80.0, 0.0)` — always include a specific edge case in addition to random ones.
* `assume(condition)` — discard inputs that do not satisfy a precondition. **Use sparingly.**
* `--hypothesis-seed=N` — reproduce a run; `--hypothesis-show-statistics` — see how many inputs were generated and discarded.

**The filtering anti-pattern.** Writing `assume(abs(a - b) < 0.01)` on two independent floats throws away nearly *every* input, and Hypothesis aborts with `FailedHealthCheck(filter_too_much)`. The fix is to **generate valid data directly** — here, a base value and a small *delta*:

```python
# verified: pytest
from hypothesis import given, strategies as st
from autotest.bms import max_charge_current

@given(st.floats(0, 99.99), st.floats(0, 0.01))
def test_taper_is_continuous(soc, delta):
    assert abs(max_charge_current(soc, 25) - max_charge_current(min(soc + delta, 100), 25)) < 1.0
```

## 10.6 Fuzzing

**Fuzzing** feeds large volumes of malformed, unexpected or random data to an interface to provoke crashes, hangs and security problems. It is property-based testing with one property: **"the system survives and fails safely."**

| Style | How inputs are made | Tools |
|---|---|---|
| **Dumb / random** | random bytes | a seeded loop (below) |
| **Mutation-based** | flip bits in valid examples (real traces) | custom scripts, AFL |
| **Generation-based** | build structured inputs from a grammar/spec | Hypothesis strategies, protocol fuzzers |
| **Coverage-guided** | evolve inputs that reach new code | AFL++, libFuzzer, Atheris (Python) |

For an automotive diagnostic server the oracle is: *for any request, the server returns a **well-formed** response (positive, or `7F <sid> <nrc>`), never raises, never hangs.*

```python
# verified: python
import random
from autotest.diagnostics import DiagnosticManager

rng = random.Random(1234)                     # SEEDED: a failure can be replayed exactly
mgr = DiagnosticManager()
for _ in range(5000):
    blob = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 12)))
    response = mgr.handle_request(blob)
    assert isinstance(response, bytes) and response
    assert response[0] in (0x7F, 0x59, 0x54, 0x62)
    if response[0] == 0x7F:
        assert len(response) == 3
print("5000 random requests: all answers well-formed")
```

Fuzzing does **not** prove security — it finds what it happens to reach. It is one layer next to design review and threat analysis (ISO/SAE 21434).

## 10.7 Stateful and model-based testing (taste)

Hypothesis can also generate **sequences of operations** against a model (`RuleBasedStateMachine`): random "power on / set / brake / …" steps with invariants checked after every step — Chapter 9's exhaustive sequences, scaled to arbitrary length. It is the natural next step for state machines with more than a handful of events.

## 10.8 Strengths, weaknesses, advice

| Strengths | Weaknesses |
|---|---|
| finds cases nobody listed (NaN, extremes, odd combinations) | needs *properties*, which require thought |
| readable minimal counter-examples (shrinking) | slower than a few examples; non-deterministic unless seeded/database-backed |
| failures are remembered and replayed | weak for "exact value" requirements |

Combine the two: **examples document and pin specific requirements; properties search for the surprises.** Always keep a fixed seed or the example database in CI so a failure reproduces.

## Check your understanding

1. Name the property pattern: "doubling a vehicle's mass never shortens its braking distance".
2. Why is "`result == the code computed again inside the test`" a poor property?
3. Hypothesis raises `FailedHealthCheck(filter_too_much)`. What went wrong and how do you fix it?
4. What is the single oracle used when fuzzing a diagnostic server?

<!--ANSWERS-->
1. A metamorphic property (a known relation between two runs of the system).
2. It re-implements the code in the test, so any bug in the logic is duplicated and the test cannot fail for the right reason. A property should state something *independent* — an invariant, a round trip, a simple reference model of the specification.
3. `assume()` or `.filter()` rejected nearly all generated inputs. Generate valid inputs directly (build the structure you need, e.g. base + small delta) instead of filtering.
4. "The server must survive and answer with a well-formed response (positive or negative) — it must never crash, hang or return garbage."
