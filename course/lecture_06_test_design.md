# Designing tests from a specification

## 6.1 The problem: you cannot test everything

`max_charge_current(soc, temp_c)` takes two real numbers. Trying every pair of 64-bit floats would take longer than the age of the universe. Yet a handful of well-chosen tests can reveal almost all defects of a certain kind. **Test design techniques** are systematic ways to choose that handful — and to be able to *defend* why it is enough.

All techniques in this chapter are **black-box**: you derive them from the *specification*, without looking at the code. That has two big benefits: the tests stay valid when the implementation is rewritten, and they can expose faults of *omission* (behaviour the code forgot) that no amount of code-based testing can find.

The specification we use throughout is the docstring of `max_charge_current`:

```
temp < 0 or temp > 45   -> 0 A
0 <= temp < 10          -> 25 % of rated
10 <= temp <= 45        -> 100 % of rated
soc >= 100              -> 0 A
soc > 80                -> taper linearly from the temperature limit to 0 at 100 %
```

## 6.2 Requirements-based testing

The first rule: **every requirement gets at least one test**, and each test says which requirement it verifies (Lab 13 automates this). Read each sentence of the spec and ask "what observable behaviour does this promise?" If you cannot state an expected result, the *requirement* is untestable and must be clarified before coding — a valuable finding in itself.

## 6.3 Equivalence partitioning

Inputs that the specification treats **identically** form an **equivalence class**. If one member of the class exposes a fault, others probably would too; if one passes, the others probably pass. So test **one representative per class**.

Partition the temperature input:

```
   (−∞, 0)        [0, 10)         [10, 45]         (45, +∞)
   too cold        cold            normal           too hot
      0 A         25 %             100 %              0 A
 representative:  −20     5          25            60
```

Rules of thumb:

* Include **valid and invalid** classes. Invalid classes (negative SOC, SOC > 100) test the error handling.
* Partition **each input**, then combine (carefully — see §6.6).
* Classes can be *derived from the output* too: "results where the current is zero" and "results where it is positive" are classes of the output.

```python
# verified: pytest
import pytest
from autotest.bms import max_charge_current

@pytest.mark.parametrize(
    "temp, expected",
    [(-20, 0.0), (5, 25.0), (25, 100.0), (60, 0.0)],
    ids=["too-cold", "cold", "normal", "too-hot"],
)
def test_temperature_partitions(temp, expected):
    assert max_charge_current(soc=50, temp_c=temp) == pytest.approx(expected)
```

## 6.4 Boundary value analysis (BVA)

Programmers make **off-by-one** mistakes (`<` vs `<=`), so defects *cluster at the edges* of classes. **BVA** adds tests *on and next to every boundary*.

For the boundary "temperature ≥ 0 is allowed", with a resolution of 0.1:

```
        −0.1        0.0        0.1
   (still too cold)  (boundary)  (just inside)
```

* **Two-value BVA:** the boundary value and its closest neighbour on the *other* side.
* **Three-value BVA** (used in this course): below, on, and above — it also catches mistakes that flip the direction of the comparison.

| Boundary | Values tested | What a defect would look like |
|---|---|---|
| 0 °C | −0.1, 0.0, 0.1 | `temp <= 0` instead of `temp < 0` |
| 10 °C | 9.9, 10.0, 10.1 | cold limit applied at exactly 10 °C |
| 45 °C | 44.9, 45.0, 45.1 | `temp >= 45` blocks charging at the allowed limit |
| 80 % SOC | 79.9, 80.0, 80.1 | taper starts a step too early or late |

For floats, "next to" means the smallest meaningful step of the specification (0.1 °C here), not the smallest representable float. When the spec says nothing about resolution, ask.

```python
# verified: pytest
import pytest
from autotest.bms import max_charge_current

@pytest.mark.parametrize(
    "temp, expected",
    [(-0.1, 0.0), (0.0, 25.0), (0.1, 25.0),
     (9.9, 25.0), (10.0, 100.0), (10.1, 100.0),
     (44.9, 100.0), (45.0, 100.0), (45.1, 0.0)],
)
def test_temperature_boundaries(temp, expected):
    assert max_charge_current(soc=50, temp_c=temp) == pytest.approx(expected)
```

## 6.5 Decision tables

When behaviour depends on a **combination of conditions**, list every combination (or every *rule*) and its expected action. Single-condition tests miss **interactions**.

| Rule | cold (0–10 °C) | soc > 80 | hot/too cold | soc ≥ 100 | Expected |
|---|---|---|---|---|---|
| R1 | no | no | no | no | full current |
| R2 | **yes** | no | no | no | 25 % |
| R3 | no | **yes** | no | no | tapered |
| R4 | **yes** | **yes** | no | no | 25 % **and** tapered |
| R5 | — | — | **yes** | — | 0 A |
| R6 | — | — | no | **yes** | 0 A |

Rule R4 is the one a developer forgets: it combines two rules that each work alone. Each row becomes one parametrized case:

```python
# verified: pytest
import pytest
from autotest.bms import max_charge_current

@pytest.mark.parametrize("soc, temp, expected", [
    (50, 25, 100.0),    # R1 normal
    (50, 5, 25.0),      # R2 cold only
    (90, 25, 50.0),     # R3 taper only
    (90, 5, 12.5),      # R4 cold AND taper: the interaction
    (50, 50, 0.0),      # R5 hot
    (100, 25, 0.0),     # R6 full
])
def test_decision_table(soc, temp, expected):
    assert max_charge_current(soc, temp) == pytest.approx(expected)
```

Decision tables also expose **specification gaps**: a combination for which no action is defined (e.g. "hot *and* soc ≥ 100": which rule wins?). Log such questions; do not guess.

## 6.6 Combinatorial explosion and pairwise testing

With *n* parameters of *k* values each, all combinations number *kⁿ*. Empirical studies of defect data repeatedly find that most failures are triggered by the interaction of **one or two** parameters, rarely more. **Pairwise (all-pairs) testing** therefore chooses a small set of tests in which *every pair of values of every pair of parameters* appears at least once.

For three on/off parameters A, B, C: 8 combinations, but 4 tests cover all pairs.

```python
# verified: python
from itertools import combinations, product

tests = [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]      # 4 instead of 8

def pairs_covered(rows):
    return {((i, a), (j, b)) for r in rows for (i, a), (j, b) in combinations(enumerate(r), 2)}

all_pairs = pairs_covered(product((0, 1), repeat=3))
assert pairs_covered(tests) == all_pairs
print(f"{len(tests)} tests cover all {len(all_pairs)} value pairs of the full {2**3}")
```

Tools such as `allpairspy` (Python) generate such sets automatically. Pairwise is excellent for **configuration** testing (variants × markets × options) and a poor substitute for a decision table when you need *specific* rule combinations.

## 6.7 Error guessing and checklists

Experience beats theory for the stubborn cases. Keep a checklist of inputs that break software, and apply it to every function:

| Category | Probe |
|---|---|
| Numbers | 0, −1, 1, max, max+1, −0.0, **NaN**, ±inf, tiny differences |
| Sizes | empty, one element, exactly full, one too many |
| Text/bytes | empty, non-ASCII, very long, embedded newline, wrong length |
| Time | wrap-around of counters, equal timestamps, going backwards |
| State | repeated call, call before initialisation, call after failure |
| Environment | missing file, unreadable device, interrupted transfer |

The NaN probe is not hypothetical: it uncovered two real safety-relevant defects in this very course's BMS (Lab 8).

## 6.8 Invariants: tests without a precise oracle

Sometimes you cannot compute the exact expected value, but you know a **property** that must hold:

* output stays within physical limits: `0 ≤ current ≤ rated` for every input;
* **monotonic**: more SOC never allows *more* current;
* **safety**: whenever temperature is outside 0–45 °C, the result is exactly zero.

Invariant checks over a grid (or, in Chapter 10, over *generated* inputs) are a cheap way to cover enormous input spaces.

## 6.9 Putting it together: a design recipe

1. List the **requirements**; mark any that are ambiguous.
2. For each input, draw the **partitions** (valid and invalid).
3. Mark every **boundary**; add three-value tests.
4. If outcomes depend on **combinations**, write the **decision table**; one row = one test.
5. Add **error-guessing** probes from the checklist.
6. Add **invariants** for properties that must always hold.
7. Write expected values **from the spec**, never by running the code.
8. Review: could a plausible fault (wrong operator, off-by-one, swapped constant) pass all these tests? (Chapter 15 measures this.)

## Check your understanding

1. A function accepts SOC from 0 to 100 inclusive. List the boundary-value test inputs (three-value BVA) with resolution 1.
2. Why does a decision table often reveal more than a set of individual boundary tests?
3. Three parameters have 4, 3 and 2 values. How many exhaustive combinations exist, and why might pairwise testing need far fewer?
4. Why must the expected value in a test come from the specification and not from running the code?

<!--ANSWERS-->
1. Lower boundary 0: −1, 0, 1. Upper boundary 100: 99, 100, 101 → −1 and 101 are invalid (expect rejection), the rest valid.
2. It forces you to enumerate *combinations* and so exposes interactions (e.g. cold *and* tapering) and specification gaps that single-condition tests never reach.
3. 4 × 3 × 2 = 24 exhaustive combinations. Pairwise only needs every *pair* of values to appear once; the largest pair is 4 × 3 = 12, so roughly a dozen tests suffice.
4. A value copied from the code's own output merely freezes the current behaviour — including any bug. The test could then never fail for a wrong result.
