# Putting it all together: building a test strategy

You now have the tools; the capstone asks you to *use* them on an unfamiliar module. This chapter is a recipe, a checklist and a list of habits to take back to real projects.

## 17.1 From specification to a test plan: a recipe

Take the TPMS specification in the capstone (S1–S9). A strategy is built in layers:

**Step 1 — Read the spec as a tester.** Underline every *number*, *comparison*, *unit* and *error condition*. Each is a potential defect site. Write down every **question** the spec leaves open — these are findings.

**Step 2 — Decompose into testable units.** Normalisation (a calculation), classification (thresholds, four outputs), validation (sensor id, ranges), leak detection (stateful, time window).

**Step 3 — Pick techniques per unit.**

| Unit | Techniques (chapter) |
|---|---|
| Normalisation formula | exact hand-computed values at cold / nominal / hot; one *property* (monotone in temperature) — (6, 10) |
| Classification | equivalence classes for the four outputs; **three-value boundaries** at every threshold; check the *default* nominal and an *override* (6) |
| Input validation | negative tests; **both sides of every inclusive limit**, on both axes; format classes for ids (6, 11) |
| Leak detector | state-based: drop sizes (just below / exactly / above the threshold), the window edge (exactly at, just after), expiry of old samples, rising pressure, slow drift; fixtures for a fresh detector each test (6, 9) |
| Whole module | one property-based test (e.g. a better pressure never yields a worse status) (10) |

**Step 4 — Design with oracles from the spec.** Compute expected values by hand or from the formulas. Never paste output from the code.

**Step 5 — Write them to be readable.** Parametrize with ids; one reason to fail per test; names that state behaviour and condition; fixtures for repeated set-up; a requirement marker on tests that verify a stated requirement.

**Step 6 — Check adequacy.** Run coverage (`--cov-branch --cov-report=term-missing`). Then ask the mutation question for every `<`, `<=`, constant and `max/min` in the spec: *which assertion fails if this is wrong?* Use `capstone/grade.py` as an independent measure.

**Step 7 — Make it maintainable.** Deterministic (no sleeps, seeded randomness), fast, independent, documented.

## 17.2 A test-plan skeleton

```
1. Scope            — what is under test, what is explicitly out of scope and why
2. References       — specification version, requirements IDs
3. Strategy         — levels, techniques, tools, environments (SIL/HIL)
4. Test design      — per unit: partitions, boundaries, decision/state tables
5. Entry / exit     — when do we start; "done" means: all requirements verified,
                      branch coverage ≥ X on safety code, mutation score ≥ Y on
                      <modules> (survivors reviewed), no open critical defects
6. Environment      — versions, simulators, fixtures, data (logs/golden files)
7. Risks            — what is hard to test and what we do about it
8. Reporting        — CI stages, artefacts (JUnit, coverage, traceability matrix)
```

## 17.3 A checklist for reviewing a test

1. Does the **name** say what behaviour and under which condition?
2. Is the **expected value** derived from the specification?
3. Is there **exactly one reason** for it to fail?
4. Would it **fail if the code were wrong** in the obvious ways (try a mutation)?
5. Is it **deterministic** (clock, randomness, ordering) and **independent**?
6. Is the *arrange* step **obvious** without hunting through fixtures?
7. Does it test **behaviour**, not implementation details, so refactoring does not break it?
8. Is it at the **right level** — could a faster, lower-level test catch the same defect?

## 17.4 Common anti-patterns (and the lab that cures them)

| Anti-pattern | Cure |
|---|---|
| Expected values copied from the code's output | derive from the spec (Ch. 6) |
| `time.sleep()` in tests | inject a clock (Ch. 7) |
| Everything mocked; assertions only on calls | state verification, real cheap collaborators (Ch. 7) |
| One giant test with many asserts | focused tests, parametrization (Ch. 5) |
| Shared mutable fixtures | function-scoped fixtures (Ch. 5) |
| Tests that depend on execution order | isolation (Ch. 4, 5) |
| "100 % coverage" as the goal | mutation score + review (Ch. 15) |
| Updating golden files to turn red → green | review diffs deliberately (Ch. 12) |
| Ignoring/retrying flaky tests | find the cause (Ch. 12) |
| Only happy-path tests | boundaries, negatives, fault injection (Ch. 6, 11) |
| Ice-cream-cone test mix | pyramid (Ch. 2) |
| No link between tests and requirements | traceability (Ch. 16) |

## 17.5 Habits to take to a real project

* **Test first, or at least test together.** For every bug: red → green → keep.
* **Make the code testable.** Inject clocks, hardware, randomness; prefer pure functions; small interfaces.
* **Automate and run constantly.** If it is not in CI, it does not exist.
* **Treat tests as production code**: review, refactor, delete dead tests.
* **Measure the tests** (coverage for gaps, mutation for strength, flakiness for trust).
* **Be honest about what is not tested** — every strategy has gaps; write them down with the risk.
* **Keep learning from escapes.** Every defect found late is a missing test *and* a question about the strategy.

## 17.6 What to do next

1. Complete the **capstone** and aim for a perfect defect-catch score.
2. Apply the **mutation tool** to your own project's most critical function.
3. Replace one slow, flaky end-to-end test with a seeded simulation or a fake clock.
4. Add a **smoke stage** and a **traceability check** to your CI.
5. Read about **TDD**, **property-based stateful testing**, **coverage-guided fuzzing**, and **MC/DC tooling** (see the reading list).

## Final self-assessment

1. Choose a function from your own work. Which of its inputs have *boundaries*? Which *combinations* matter? What *hostile* values could reach it?
2. Which collaborators would you replace with doubles, and what *seam* would you add to allow it?
3. What *property* must hold for every input? What *safety* property?
4. How would you know your tests are strong enough — which number would you look at, and what would it *not* tell you?

<!--ANSWERS-->
These questions have no single right answer; compare your reasoning with the recipe in §17.1 and the techniques in Chapters 6, 7, 10, 11 and 15. A strong answer names concrete boundary values and hostile inputs (NaN, empty, wrap-around), identifies a seam (clock, hardware, bus), states at least one invariant and one safety property, and pairs coverage (what is untested) with mutation score (what is not checked) while acknowledging that neither proves correctness.
