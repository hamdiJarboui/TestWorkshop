# Further reading and resources

## Testing fundamentals
* Glenford J. Myers, Corey Sandler, Tom Badgett — *The Art of Software Testing*. The classic that introduced equivalence classes and boundary analysis to many engineers.
* Paul Ammann and Jeff Offutt — *Introduction to Software Testing*. Rigorous treatment of coverage criteria (including MC/DC) and mutation testing.
* Paul C. Jorgensen — *Software Testing: A Craftsman's Approach*. Test-design techniques in depth.
* ISTQB — *Foundation Level syllabus* (free). The seven principles and a common vocabulary.
* ISO/IEC/IEEE 29119 — *Software testing* (vocabulary, processes, documentation).

## Python testing
* Brian Okken — *Python Testing with pytest*. Practical, thorough guide to fixtures, parametrization and plugins.
* The official documentation: **docs.python.org** (`unittest`, `unittest.mock`), **docs.pytest.org**, **hypothesis.readthedocs.io**, **coverage.readthedocs.io**.
* David R. MacIver — articles on the philosophy of Hypothesis and property-based testing ("What is property-based testing?").

## Design for testability and doubles
* Gerard Meszaros — *xUnit Test Patterns: Refactoring Test Code*. Source of the test-double taxonomy and many test smells.
* Kent Beck — *Test-Driven Development: By Example*.
* Steve Freeman and Nat Pryce — *Growing Object-Oriented Software, Guided by Tests*.
* Martin Fowler — article *Mocks Aren't Stubs* (classicist vs mockist styles).

## Robustness and resilience
* Michael T. Nygard — *Release It!* Patterns for stability under failure.
* Articles and documentation on coverage-guided fuzzing: AFL++, libFuzzer, Atheris (Python).

## Automotive and safety
* ISO 26262 *Road vehicles — Functional safety*, Part 6 (product development at the software level) and Part 8 (supporting processes).
* Automotive SPICE *Process Assessment / Reference Model* (VDA QMC) — SWE.4, SWE.5, SWE.6.
* AUTOSAR *Specification of SW-C End-to-End Communication Protection Library* (E2E profiles).
* ISO 11898 (CAN), ISO 14229 (UDS), ISO/SAE 21434 (cybersecurity engineering).
* Robert Bosch GmbH — *Bosch Automotive Handbook* for vehicle dynamics and ABS background.

## Control and simulation
* Karl Åström and Richard Murray — *Feedback Systems: An Introduction for Scientists and Engineers* (free from the authors).
* Rajesh Rajamani — *Vehicle Dynamics and Control* (longitudinal control, ABS).
* The FMI standard (fmi-standard.org) for co-simulation.

## Tools to explore next
`pytest-xdist` (parallel), `pytest-bdd` (Gherkin), `mutmut` / `cosmic-ray` (mutation), `python-can` and `cantools` (real CAN logs and DBC files), `tox`/`nox` (environment matrices), `ruff`/`mypy` (static analysis), `allpairspy` (pairwise generation).
