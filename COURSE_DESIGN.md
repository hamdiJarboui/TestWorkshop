# Course design — Testing with Python: unittest, pytest & Automotive Software

## 1. Audience and prerequisites
* **Audience:** software/embedded/validation engineers, students in automotive or mechatronics programmes, test engineers moving from manual to automated testing.
* **Prerequisites:** working Python (functions, classes, exceptions, modules, `pip`); basic Git; no automotive background needed — every domain concept (CAN, DTC, SOC, ABS slip) is explained where first used.
* **Environment:** Python ≥ 3.10, `pip install -r requirements.txt` (pytest, pytest-cov, hypothesis). No hardware.

## 2. Learning outcomes
On completion a learner can:

| # | Outcome | Bloom level | Labs |
|---|---------|-------------|------|
| LO1 | Write, run and organise unit tests with both `unittest` and `pytest` and explain when each fits | Apply | 1, 2 |
| LO2 | Derive test cases from a specification using equivalence classes, boundary values, decision tables and state models | Apply / Analyse | 3, 6 |
| LO3 | Isolate a unit with the right test double and make time and hardware deterministic | Apply | 4 |
| LO4 | Verify component interfaces, including timing, protection and fault behaviour, through integration and contract tests | Analyse | 5 |
| LO5 | Formulate properties and use generative/fuzz testing to find defects no one anticipated | Analyse | 7, 8 |
| LO6 | Design fault-injection and robustness tests; judge whether a system fails safely | Evaluate | 8 |
| LO7 | Protect against regressions with bug-guard tests, golden files and recorded-log replay | Apply | 9 |
| LO8 | Specify and test performance budgets, scaling and memory behaviour without flaky tests | Apply / Evaluate | 10 |
| LO9 | Verify closed-loop behaviour against measurable acceptance criteria using plant simulation (SIL) | Analyse / Evaluate | 11 |
| LO10 | Assess the adequacy of a test suite with coverage **and** mutation analysis and interpret survivors | Evaluate | 12 |
| LO11 | Trace requirements to tests and results; run the same test on simulation and hardware | Apply / Create | 13 |
| LO12 | Plan, build and justify a complete test strategy for an unfamiliar module and measure its effectiveness | Create | Capstone |

## 3. Schedule

### Intensive — 5 days × 7 h (≈ 35 h)
Each lab below is preceded by its lecture chapter (Chapters 4–16 pair with Labs 1–13 in order; Chapter 17 introduces the capstone).

| Day | Morning (3.5 h) | Afternoon (3.5 h) |
|-----|----------------|-------------------|
| 1 | Chapters 1–3 foundations (1.5 h) · Ch. 4 + **Lab 1** unittest | Ch. 5 + **Lab 2** pytest |
| 2 | **Lab 3** black-box design | **Lab 4** doubles · start **Lab 5** |
| 3 | Finish **Lab 5** integration · **Lab 6** state machines | **Lab 7** property-based |
| 4 | **Lab 8** robustness · **Lab 9** regression | **Lab 10** performance (short) · **Lab 11** SIL |
| 5 | **Lab 12** coverage & mutation · **Lab 13** traceability | **Capstone** + presentations of strategies |

### Part-time — 10 weeks × 3 h
W1 L1 · W2 L2 · W3 L3 · W4 L4+L5 (part) · W5 L5+L6 · W6 L7 · W7 L8 · W8 L9+L10 · W9 L11+L12 · W10 L13 + capstone review. Capstone is homework from W7.

## 4. Pedagogy
0. **Lecture, then lab.** Each lab is preceded by a lecture chapter (`course/`, 30–60 min of reading or teaching) that explains the concepts, techniques and automotive background; Chapters 1–3 are foundations (testing vocabulary, the landscape of test types/levels, an automotive primer). Every code example in the lectures is executed by `tools/check_course_code.py`, so the text cannot drift from the code.
1. **One system under test for the whole course.** Learners meet the same library again and again, so effort goes into *testing technique*, not into learning new code. Later labs build on earlier ones (Lab 3's suite is the input of Lab 12's mutation run; Lab 9's replay exposes a defect that integration tests in Lab 5 missed).
2. **Worked example → break it → exercise → debrief.** Every worked test file is commented teaching material; every lab README has a "Try this" mutation to build the intuition that *a test is only as good as the defect it would catch*.
3. **Real defects, not only contrived ones.** Four findings were discovered while *building* the course and are kept in as case studies: BUG-130 (a bit error costs two frames — Lab 9), BUG-201/202 (NaN falls through every safety comparison — Lab 8), a redundant `soc >= 100` guard revealed by mutation analysis (Lab 12), and an O(window) leak detector (Lab 10). Other ticket numbers (BUG-087, 093, 114, 120) are teaching scenarios.
4. **Red → green discipline.** Strict `xfail` pins known bugs; solutions are executable so they cannot drift from the code.
5. **Determinism as a design principle.** Injected clocks, seeded RNGs, no sleeps, no network.
6. **Pair work** on Labs 5, 8 and 13 (one drives, one challenges "what would make this pass wrongly?").

## 5. Assessment
| Component | Weight | Evidence |
|---|---|---|
| Lab exercises (13) | 30 % | `exercise_labNN.py` completed; spot-checked against `solutions/`, graded on correctness *and* test quality |
| Quiz after Lab 7 and Lab 12 | 20 % | See §6 |
| Capstone | 50 % | `capstone/grade.py` score, code review, ≤ 1-page report (rubric in `capstone/README.md`) |

**Test-quality rubric** (use for exercises and capstone): *names state behaviour* · *one reason to fail* · *boundaries chosen deliberately* · *deterministic* · *asserts outcomes, not implementation* · *fails for the right reason* (show that by breaking the code) · *no duplicated logic from the SUT*.

## 6. Sample quiz questions
1. A test passes both before and after you delete the line under test. What does that tell you? (Lab 12)
2. Why is `assertEqual(0.1 + 0.2, 0.3)` a bad test and what are two fixes? (Lab 1/2)
3. List the boundary values you would test for "charging allowed between 0 °C and 45 °C inclusive". (Lab 3)
4. You patch `autotest.can.e2e_protect` but the test still sends real CRCs. Why? (Lab 4)
5. Name two defects found only by an integration test. (Lab 5)
6. Give three properties of a CAN signal codec. Which would catch a wrong sign extension? (Lab 7)
7. Why is `xfail(strict=True)` better than `xfail` for a known bug? (Lab 8)
8. When is changing a golden file legitimate? (Lab 9)
9. Why assert p99 against a 10× budget rather than the mean against the expected time? (Lab 10)
10. A suite has 100 % branch coverage and 4 % mutation score. Explain how that is possible. (Lab 12)

## 7. Standards alignment (informative)
The course is **not** a compliance training; it shows the *techniques* these standards ask for. Check clause numbers against the edition your organisation uses.

| Topic | Where it shows up |
|---|---|
| ISO 26262-6 software unit verification — requirements-based tests, interface tests, fault injection, resource-usage evaluation, equivalence classes, boundary values, error guessing | Labs 3, 4, 5, 8, 10 |
| ISO 26262-6 structural coverage (statement / branch / MC/DC by ASIL) | Lab 12 |
| ISO 26262-6 software integration & verification of software requirements; ASPICE SWE.4 / SWE.5 / SWE.6 | Labs 5, 11, 13 |
| Bidirectional traceability (requirement ⇄ test ⇄ result) | Lab 13 |
| AUTOSAR E2E-style protection (CRC + alive counter) | Labs 1, 5, 7, 8, 9 |
| ISO 14229 UDS — negative response codes, DTC handling | Labs 8, 9, 13 |
| Cybersecurity testing mindset (ISO/SAE 21434) — fuzzing the diagnostic interface | Lab 8 |
| X-in-the-loop (MIL/SIL/HIL) | Labs 11, 13 |

## 8. Design decisions and trade-offs
* **Simulated, simplified models.** Enough physics to make closed-loop tests meaningful (peak friction at 20 % slip, drag + rolling + grade) but small enough to read in minutes. They are not validated vehicle models.
* **`unittest` first, then `pytest`.** Learners see the vocabulary the standard library gives them (and the boilerplate it costs) before pytest removes it; Lab 1's tests also run unchanged under pytest, demonstrating migration.
* **Own mutation tester (`tools/mini_mutate.py`).** ~120 lines students can read. Production tools (mutmut, cosmic-ray) are named in Lab 12 for real projects.
* **Exercises are separate from worked tests** (`exercise_*.py` is not collected by default) so `make test` stays green for CI while students iterate on red exercises.
* **Timing tests use big margins** and a separate CI stage; the course explicitly teaches why host timing ≠ target WCET.

## 9. Extension ideas
`pytest-xdist` for parallel runs · `pytest-bdd` for Gherkin acceptance tests · `mutmut` on the full package · `tox`/`nox` matrices · `python-can` + `cantools` with real DBC/ASC files · `pyserial`/`PCAN` driver behind the `hil` fixture · `mypy`/`ruff` as static-analysis labs · MC/DC analysis with a coverage tool that supports it · a second capstone on the BMS or ABS controller.
