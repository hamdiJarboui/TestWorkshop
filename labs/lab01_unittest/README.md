# Lab 1 — Unit testing with `unittest`

> **Read first:** Chapter 4 — *unittest: the standard library's test framework* (`course/lecture_04_unittest.md`).

**Duration:** 2.5 h · **Type:** unit testing · **Code under test:** `can.py`, `sensors.py`, `bms.py`

## Why it matters in a vehicle programme
A modern car runs 100M+ lines of code; the cheapest place to find a defect is the unit that contains it.
A wrong CAN scale factor or a CRC off-by-one is invisible on the bench but costs a recall in the field.
`unittest` ships with Python, so it works in locked-down toolchains where installing packages is hard.

## Learning objectives
After this lab you can: write a `TestCase`; choose the right `assert*` method; test exceptions and floating-point
results; share set-up safely (`setUp`, `setUpClass`); run many inputs with `subTest`; document skipped and known-failing
tests; run tests from the CLI, as a hand-built suite, or through pytest.

## Concepts (10 min)
* **Anatomy:** Arrange → Act → Assert. A unit test fails for exactly one reason.
* **Isolation:** `setUp` runs before *every* test, so tests cannot depend on each other.
* **`subTest`:** reports each failing input separately instead of stopping at the first.
* **Never `assertEqual` floats** — use `assertAlmostEqual`.
* **`expectedFailure` / `skip`** make known problems visible instead of deleting tests.

## Run it
```bash
python -m unittest discover -s labs/lab01_unittest -p "test_lab01*.py" -v     # (needs `pip install -r requirements.txt`; otherwise prefix with PYTHONPATH=src)
pytest labs/lab01_unittest -v          # same tests, pytest runner
```

## Guided tour of `test_lab01_unittest.py`
| Class | Look for |
|---|---|
| `TestUnitConversions` | `subTest`, `assertAlmostEqual`, `assertRaisesRegex` — also the hand-computed expected value (14.4 km/h) |
| `TestCrc8` | A *catalogue check value* (0x4B) is the best oracle you can get; single-bit-flip loop proves CRC strength |
| `TestCANFrame` | `setUp`/`tearDown`; frozen dataclass; boundary 0x7FF/0x800 |
| `TestSignalScaling` | `setUpClass`, `@skip`, `@expectedFailure` documenting a known resolution defect |
| `load_tests` | building a suite by hand |

**Try this (5 min):** in `can.py` change `& 0xFF` in `crc8` to `& 0x7F`. Which tests fail, and which do *not*? What does that tell you about the suite?

## Exercises — `exercise_lab01.py`
*Run:* `python course.py exercise 1` — the tests start red (most with a `todo(...)` line: delete it when you start on that test). Hints are in each test's docstring; read them one at a time.

1. Coulomb counting in `BatteryManagementSystem.update_soc`: clamping, discharge, invalid input.
2. Encode/decode a two-signal engine message — work out the expected bytes **by hand first**.
3. E2E protection: round trip, corruption, counter wrap.

## Debrief questions
* Why is `assertTrue(a == b)` a worse choice than `assertEqual(a, b)`?
* A test uses `setUpClass` to create a battery object and mutates it. What can go wrong?
* When is an `expectedFailure` better than a skipped test? Than a deleted test?

## Common pitfalls
Tests that depend on execution order · asserting on `repr`/exception text that may legitimately change ·
catching exceptions manually (`try/except` hides "no exception" passing silently) · testing the implementation instead of behaviour.
