# Requirements, traceability, standards and continuous integration

## 16.1 Tests only mean something relative to requirements

Every test answers "does the software do what it *should*?" — so *what it should do* must be written down. Requirements are the oracle for the whole project, and the connection between a requirement and the tests that verify it is called **traceability**.

### What makes a requirement testable?

| Property | Bad | Good |
|---|---|---|
| **Unambiguous** | "charging shall be safe when cold" | "charging shall be inhibited below 0 °C and limited to 25 % of rated current from 0 to <10 °C" |
| **Measurable** | "the display shall update quickly" | "the cluster shall show `--` when no valid speed frame arrived for 100 ms" |
| **Atomic** | one sentence, five obligations | one verifiable obligation, one ID |
| **Identified** | in a paragraph | `REQ-CLU-001` |
| **Feasible & necessary** | gold-plated | traceable to a safety goal or stakeholder need |

If you cannot write a pass/fail criterion, send the requirement back. *Ambiguity found while designing tests is the cheapest defect you will ever find.*

## 16.2 Traceability: requirement ⇄ test ⇄ result

An assessor (ISO 26262, Automotive SPICE) asks: *"Show me which test verifies requirement X — and its latest result."* **Bidirectional traceability** answers that in both directions:

```
requirement ──verified by──► test case(s) ──executed in──► test run ──► verdict
     ▲                                                                    │
     └─────────────── coverage: every requirement has ≥ 1 test ◄──────────┘
                      every test cites ≥ 1 requirement (no orphan tests)
```

In this course the link is a custom pytest **marker**:

```python
import pytest

@pytest.mark.requirement("REQ-CLU-001")
def test_cluster_blanks_after_100ms_without_frames(bus, clock):
    ...                      # arrange / act / assert go here
```

and a small plugin in `conftest.py` collects the markers and prints a matrix (`pytest --req-report`):

```
REQ-BMS-001    PASS  (14 tests)
REQ-CAN-003    PASS  (4 tests)
REQ-CLU-001    PASS  (2 tests)
```

Two *meta-tests* make the traceability itself checkable, so it cannot rot:

```python
# verified: python
import re

REQUIREMENTS = {"REQ-BMS-001", "REQ-BMS-002", "REQ-CC-001"}               # from the requirements database
TEST_SOURCE = '''
@pytest.mark.requirement("REQ-BMS-001")
def test_cold(): ...
@pytest.mark.requirement("REQ-CC-001")
def test_set_range(): ...
@pytest.mark.requirement("REQ-XYZ-999")
def test_typo(): ...
'''
cited = set(re.findall(r'mark\.requirement\("(REQ-[A-Z]+-\d{3})"\)', TEST_SOURCE))

untested = sorted(REQUIREMENTS - cited)        # requirements nobody verifies
unknown = sorted(cited - REQUIREMENTS)         # tests citing deleted/mistyped requirements
print("requirements without tests:", untested)
print("tests citing unknown requirements:", unknown)
assert untested == ["REQ-BMS-002"] and unknown == ["REQ-XYZ-999"]
```

**A trap:** a PASS in the matrix proves a test *ran* and passed — not that it checks the requirement's numbers. Pair traceability with adequacy measures (Chapter 15) and review.

## 16.3 Acceptance tests and scenarios

**Acceptance tests** express requirements in the stakeholder's language and decide whether the product is *accepted*. The *Given / When / Then* form (also called **BDD** — behaviour-driven development) keeps them readable:

```
Feature: Over-voltage protection
  Scenario: One weak cell in a healthy pack
    Given a 96-cell pack where every cell is at 3.9 V
    When  one cell rises to 4.21 V
    Then  an overvoltage fault is raised
```

You can implement them as plain pytest tests with Given/When/Then comments (as Lab 13 does), or with a tool such as `pytest-bdd` that binds Gherkin text to step functions. Plain tests are enough until non-programmers must author the scenarios.

## 16.4 Functional safety standards in the verification flow

| Standard | What it asks of verification (high level) |
|---|---|
| **ISO 26262** (functional safety of road vehicles) | Verification at each level of the V-model with methods and rigour scaled by **ASIL**: requirements-based tests, interface tests, fault injection, resource-usage tests, structural coverage; evidence and traceability in the safety case; independence of reviewers/testers at higher ASILs |
| **Automotive SPICE** (process assessment) | Defined processes for unit verification, component/integration verification and software qualification test, with traceability and consistency between requirements, design and tests |
| **ISO/SAE 21434** (cybersecurity engineering) | Verification includes vulnerability analysis and penetration/fuzz testing of external interfaces |
| **ISO/IEC/IEEE 29119** (software testing) | General vocabulary, test processes and documentation templates |

These standards describe *what evidence* to produce, not which tool to use. The techniques of this book — requirements-based design, boundary analysis, fault injection, coverage, traceability, automation — are how that evidence is generated. *(Consult the edition and tailoring that apply to your project and your safety manager; this book is not a compliance guide.)*

## 16.5 Continuous integration: tests run themselves

A test that nobody runs protects nothing. **Continuous integration (CI)** runs the suite automatically on every change, so a regression is reported within minutes to the author who caused it. Organise the pipeline as **stages**, cheapest and fastest first:

```
commit ─► [1 smoke] ─► [2 unit + integration + coverage] ─► [3 performance]
            ~10 s        ~1 min · JUnit + coverage            ~10 s · isolated runner
                                                                    │
                  ┌─────────────────────────────────────────────────┘
                  ▼
          [4 tests of the tests] ─► [5 nightly: SIL sweeps, HIL]
          ~1 min · mutation, grader   hours · reports archived
```

A GitHub Actions workflow for this course (excerpt):

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix: { python: ["3.10", "3.11", "3.12", "3.13"] }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python }}" }
      - run: pip install -r requirements.txt
      - run: pytest -m smoke -q
      - run: pytest -m "not slow and not performance" --cov=autotest --cov-branch --junitxml=report.xml
      - run: pytest -m performance -q
      - run: pytest -m slow -q
      - uses: actions/upload-artifact@v4
        with: { name: reports, path: "report.xml\ncoverage.xml" }
```

Good CI habits:

* **Fail fast; keep the main branch green.** A red main branch teaches everyone to ignore red.
* **Publish artefacts**: JUnit XML (test results), coverage, traceability matrix — they *are* the audit evidence.
* **Matrix** across supported Python versions/platforms.
* **Quarantine flaky tests visibly** (tracked ticket, deadline), never ignore them silently.
* **Keep it fast.** A 40-minute pipeline is skipped; tier the slow tests (smoke → unit → nightly).

## 16.6 One test body, many back-ends: SIL and HIL

The *same* requirement should be verified on the simulator and, later, on the bench. Write the test against an **abstraction** and let a fixture supply the back-end; hardware-only variants are **skipped automatically** when no hardware is present:

```python
# verified: pytest
import pytest
from autotest.sensors import TemperatureSensor

class SimulatedADC:
    def read(self): return 2048

@pytest.fixture(params=["sil", "hil"])
def adc(request):
    if request.param == "hil":
        pytest.skip("no hardware bench connected")       # in a real lab: return BenchADC(port=...)
    return SimulatedADC()

def test_mid_scale_temperature_is_plausible_on_every_back_end(adc):
    assert -40 < TemperatureSensor(adc).read() < 150
```

On a build server this runs once and reports one skipped variant; on the HIL bench the same test runs twice. This is how test assets are *reused across the X-in-the-loop stages*. Real bench adapters must also manage **safe state on abort**, **nondeterministic timing**, and **limited test time** — which is why only what *needs* hardware is run there.

## 16.7 Metrics that matter (and those that mislead)

| Useful | Misleading on its own |
|---|---|
| requirements covered / verified / failing | raw test count |
| branch coverage + mutation score on safety logic | overall coverage percentage as a target |
| flaky-test rate; mean time to detect | "tests per developer" |
| defect escape rate (found after release) | pass rate with no context |
| pipeline duration (feedback time) | lines of test code |

## Check your understanding

1. Rewrite "the system shall react fast to a lost frame" as a testable requirement.
2. What two failure modes do the traceability meta-tests detect?
3. Why order a CI pipeline smoke → unit → performance → nightly?
4. How does a `params=["sil", "hil"]` fixture let one test serve both a simulator and a bench?

<!--ANSWERS-->
1. For example: "When no valid wheel-speed frame has been received for 100 ms, the instrument cluster shall display `--` (REQ-CLU-001)." — unambiguous, measurable, identified.
2. Requirements with no verifying test (gaps) and tests that cite non-existent requirements (typos, stale references / orphan tests).
3. Fast checks give the quickest feedback and fail early without spending time on slow stages; expensive stages (stable timing, hours-long HIL) run only when the cheap ones pass or on a schedule.
4. The fixture supplies a different back-end per parameter while the test body is unchanged; the `hil` variant is skipped unless hardware is available (or `--hil` is passed), so it only runs on the bench.
