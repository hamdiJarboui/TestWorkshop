# Test adequacy: coverage and mutation testing

## 15.1 "Are my tests any good?"

You have a suite and it is green. Does that mean the software is well tested? **Test adequacy** criteria try to answer this. Two families exist:

* **Coverage** — what fraction of the *code* (or *requirements*) did the tests execute?
* **Mutation testing** — if the code were *wrong*, would any test notice?

The difference is the whole point of this chapter: **coverage measures what ran; mutation measures what was checked.**

## 15.2 Structural coverage criteria

Structural (white-box) criteria are defined on the control-flow of the code. From weakest to strongest:

| Criterion | A test set achieves it when… | Example weakness |
|---|---|---|
| **Statement** (line) | every statement executes | an `if` without `else` can be "covered" while its false case is never tried |
| **Branch** (decision) | every decision has been both true and false | `a and b` can be covered while `b` never decides anything |
| **Condition** | every atomic condition has been both true and false | the *combination* may never occur |
| **Condition/decision** | both of the above | does not show each condition *matters* |
| **MC/DC** (modified condition/decision) | additionally, each condition has been shown to **independently affect** the decision's outcome | the strongest practical criterion; needs *n + 1* tests for *n* conditions |
| **Path** | every path through the function | exponential; impractical beyond small functions |

### Statement vs branch: a real measurement

```python
# verified: python
import json, os, sys, tempfile, textwrap
import coverage

SRC = textwrap.dedent('''
    def clamp_soc(x):
        if x > 100:
            x = 100
        return x
''')

with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "clamp_mod.py")
    open(path, "w").write(SRC)
    sys.path.insert(0, tmp)
    cov = coverage.Coverage(branch=True, include=[path], data_file=None)
    cov.start()
    import clamp_mod
    assert clamp_mod.clamp_soc(150) == 100          # ONE test: only the 'true' side of the if
    cov.stop()
    report = os.path.join(tmp, "cov.json")
    cov.json_report(outfile=report)
    t = json.load(open(report))["files"][path]["summary"]
    print(f"statements {t['covered_lines']}/{t['num_statements']}   branches {t['covered_branches']}/{t['num_branches']}")
    assert t["covered_lines"] == t["num_statements"]             # 100 % statement coverage ...
    assert t["covered_branches"] < t["num_branches"]             # ... but the 'x <= 100' case never ran
```

One test achieves 100 % **statement** coverage yet leaves half the **branches** untried — the case where `x` is already ≤ 100 (and an `else`-style bug there would be invisible). That is why safety standards demand branch coverage at least.

### MC/DC in one example
For a decision `A or B` such as `temp < 0 or temp > 45`, MC/DC needs three tests, each *pair* demonstrating one condition's independent effect:

| Test | `temp < 0` | `temp > 45` | Decision | Used to show |
|---|---|---|---|---|
| t1 (temp = −5) | **T** | F | T | A matters (compare with t2) |
| t2 (temp = 25) | F | F | F | baseline |
| t3 (temp = 60) | F | **T** | T | B matters (compare with t2) |

For three conditions there are 2³ = 8 combinations, but only *n + 1* = 4 are needed. The snippet below searches for a minimal MC/DC set for `a and (b or c)`:

```python
# verified: python
from itertools import combinations, product

def decision(a, b, c):
    return a and (b or c)

rows = list(product((False, True), repeat=3))

def independent(cond_index, test_set):
    """Is there a pair in the set that differs ONLY in this condition and flips the outcome?"""
    for r1, r2 in combinations(test_set, 2):
        diff = [i for i in range(3) if r1[i] != r2[i]]
        if diff == [cond_index] and decision(*r1) != decision(*r2):
            return True
    return False

minimal = next(s for k in range(2, 9) for s in combinations(rows, k)
               if all(independent(i, s) for i in range(3)))
print(len(minimal), "tests suffice (n+1 = 4):", minimal)
assert len(minimal) == 4
```

In ISO 26262 the recommended coverage metric rises with the ASIL: statement and branch coverage broadly, and **MC/DC for the most demanding levels** (check the exact table in your edition).

### Coverage in practice
```bash
pytest --cov=autotest --cov-branch --cov-report=term-missing     # line + branch, show uncovered lines
pytest --cov=autotest --cov-branch --cov-report=html             # browse annotated source in htmlcov/
```
`term-missing` lists the uncovered lines and *partial branches* (e.g. `30->32`): your to-do list for new tests.

## 15.3 What coverage cannot tell you

* It says nothing about **assertions**. A test that calls everything and asserts nothing yields 100 % coverage.
* It cannot find **missing code** — a requirement you forgot to implement has no lines to cover.
* High coverage with weak checks is **false confidence**; low coverage is **real** information (that code is untested).

Use coverage as a **negative indicator** — *what is definitely untested?* — not as a quality score. Setting "90 % coverage" as a target invites tests written to move the number.

## 15.4 Mutation testing: testing the tests

**Idea.** Make a small deliberate change (a **mutant**) to the code — flip `<` to `<=`, change a constant, swap `+` for `-` — and run the tests.

* If a test **fails** → the mutant is **killed** (good: your tests noticed).
* If all tests **pass** → the mutant **survives**: either a test is missing/weak, or the mutation does not change behaviour (*equivalent mutant*).

```
original:   if temp_c > 45:   return 0.0
mutant 1:   if temp_c >= 45:  return 0.0     ← killed only by a test AT exactly 45 °C
mutant 2:   if temp_c > 46:   return 0.0     ← killed only by a test at 46 (or 45.5)
```

The theory rests on two hypotheses: the **competent programmer hypothesis** (real bugs are small deviations from correct code) and the **coupling effect** (tests that catch simple faults also catch complex ones). Mutation analysis dates to the late 1970s (DeMillo, Lipton and Sayward).

**A mutation score** is `killed ÷ total mutants` (excluding equivalent mutants where recognised).

### By hand
```python
# verified: python
def limit(temp_c):                 # code under test
    if temp_c < 0 or temp_c > 45:
        return 0.0
    return 100.0

MUTANTS = {
    "< -> <=":     lambda t: 0.0 if (t <= 0 or t > 45) else 100.0,
    "> -> >=":     lambda t: 0.0 if (t < 0 or t >= 45) else 100.0,
    "45 -> 46":    lambda t: 0.0 if (t < 0 or t > 46) else 100.0,
    "or -> and":   lambda t: 0.0 if (t < 0 and t > 45) else 100.0,
}

weak = [lambda f: f(25) == 100.0]                                    # runs the code, barely checks it
strong = weak + [lambda f: f(-0.1) == 0.0, lambda f: f(0) == 100.0,  # boundary tests (Chapter 6)
                 lambda f: f(45) == 100.0, lambda f: f(45.1) == 0.0]

def killed(suite):
    return {name for name, m in MUTANTS.items() if not all(check(m) for check in suite)}

assert all(check(limit) for check in strong)               # both suites pass on the CORRECT code
print("weak suite kills  :", sorted(killed(weak)))
print("strong suite kills:", sorted(killed(strong)))
assert killed(weak) == set()                              # not one mutant is noticed
assert killed(strong) == set(MUTANTS)
```

The *weak* suite passes on the correct code, yet **every** mutant survives — nothing in it would notice a wrong operator or constant. The boundary tests from Chapter 6 kill them all.

### Equivalent mutants
Some mutants cannot be killed because they **do not change observable behaviour**. In `max_charge_current`, replacing `soc >= 100` by `soc > 100` changes nothing: at exactly 100 the taper formula `(100 − soc)/20` already yields 0 A. Such survivors are not noise — they often mean the original line is **redundant code** — but recognising them is a human judgement. A mutation score of 100 % is therefore neither achievable nor a sensible gate.

## 15.5 Mutation testing in practice

| Aspect | Advice |
|---|---|
| **Tools** | Python: `mutmut`, `cosmic-ray`; Java: PIT; C/C++: Mull, Dextool. This course uses the readable `tools/mini_mutate.py`. |
| **Cost** | Every mutant needs a test run: scope it (one function, one module), run it nightly or on changed code only. |
| **Where** | Safety-critical logic: limit checks, state machines, arithmetic with boundaries. |
| **Reading results** | For each survivor ask: *which assertion should have failed?* Add it, or classify as equivalent. |

A pitfall learned the hard way while building this course: the first version of `mini_mutate.py` gave **different scores on identical runs**. Python validates cached bytecode by source *mtime in whole seconds* and file *size*; two same-length mutants written within one second silently reused the previous mutant's compiled code. Setting `PYTHONDONTWRITEBYTECODE=1` for the test subprocess fixed it. **When a test tool disagrees with itself, suspect the environment before the tests.**

## 15.6 Other adequacy measures

* **Requirements coverage** — every requirement has ≥ 1 verifying test (Chapter 16): catches *missing* tests that structural coverage cannot.
* **Fault-injection coverage** — every safety mechanism has been exercised by an injected fault.
* **Defect-based metrics** — defects found per test level, escape rate (defects found *after* release), time-to-fix — the ultimate feedback loop.

## 15.7 Putting the measures together

| Question | Measure |
|---|---|
| Is any code never executed by tests? | line + branch coverage |
| Do decisions with several conditions get proper checking? | MC/DC (at higher ASILs) |
| Would a wrong operator or constant be noticed? | mutation score |
| Is every requirement verified? | requirements coverage |
| Is the suite trustworthy? | flakiness rate, test failures vs. real bugs |

## Check your understanding

1. A single test calls `clamp_soc(150)` on `if x > 100: x = 100; return x`. What are the statement and branch coverages?
2. How many tests does MC/DC need for a decision with four conditions, at minimum?
3. What does a surviving mutant tell you, and what are the two possible explanations?
4. Why is "we have 95 % coverage" not evidence the tests are good?

<!--ANSWERS-->
1. Statement coverage 100 % (every line ran). Branch coverage 50 % — the `False` outcome of the `if` was never taken.
2. At least n + 1 = 5.
3. No test failed when the code was altered. Either a test is missing or too weak to notice that behaviour, or the mutant is *equivalent* (it does not change observable behaviour, so no test could kill it).
4. Coverage counts executed lines, not verified behaviour. A test with no assertions can reach 95 %; mutation testing (or review) is needed to show the assertions would actually detect faults.
