# unittest: the standard library's test framework

## 4.1 Where it comes from

`unittest` is Python's built-in member of the **xUnit** family, which began with Kent Beck's *SUnit* for Smalltalk and spread through JUnit (Java), NUnit (.NET) and PyUnit — Python's original name for it. Every xUnit framework shares the same vocabulary: *test case*, *fixture*, *suite*, *runner*, *assertion*. Learn it once and JUnit, GoogleTest and Unity/CppUTest (common in embedded C) will feel familiar.

Why start here?

* It ships with Python — no installation, which matters on locked-down build servers and in certified toolchains.
* It teaches the **concepts** (fixtures, lifecycle, isolation) explicitly, because you must write them out.
* pytest runs `unittest` tests unchanged, so nothing you write here is wasted.

## 4.2 The five core concepts

| Concept | Class | Role |
|---|---|---|
| **Test case** | `unittest.TestCase` | A class whose `test_*` methods are individual tests |
| **Fixture** | `setUp` / `tearDown` … | Code that prepares and cleans the environment |
| **Test suite** | `unittest.TestSuite` | A collection of tests or other suites |
| **Test loader** | `unittest.TestLoader` | Finds tests (by module, class or directory) and builds suites |
| **Test runner** | `TextTestRunner` | Executes a suite and reports a `TestResult` |

Most of the time you only write test cases; the command line does the rest.

## 4.3 Your first test case

```python
# verified: python
import unittest
from autotest.sensors import kmh_to_ms

class TestSpeedConversion(unittest.TestCase):
    def test_36_kmh_is_10_ms(self):
        self.assertAlmostEqual(kmh_to_ms(36.0), 10.0)

    def test_zero_stays_zero(self):
        self.assertEqual(kmh_to_ms(0), 0)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSpeedConversion)
result = unittest.TextTestRunner(verbosity=0).run(suite)
assert result.wasSuccessful() and result.testsRun == 2
```

Rules the framework applies:

* The class must inherit from `unittest.TestCase`.
* Only methods whose names **start with `test`** are run.
* Each test method runs on a **fresh instance** of the class — instance attributes set in one test are *not* visible in another. This is the foundation of test independence.
* A test **passes** if it returns normally, **fails** if an assertion raises `AssertionError`, and is an **error** if any other exception escapes (the test itself is broken or the code crashed unexpectedly).

## 4.4 The fixture lifecycle

Fixtures are the answer to: *"how do I prepare the same starting situation for many tests without copy-pasting?"* `unittest` provides hooks at three scopes:

```
setUpModule()                    once per module
  setUpClass()                   once per class        (a @classmethod)
    setUp()                      before EVERY test method
      test_a()
    tearDown()                   after EVERY test method (even if the test failed)
    setUp()
      test_b()
    tearDown()
  tearDownClass()
tearDownModule()
```

You can watch the order yourself:

```python
# verified: python
import unittest

events = []

def setUpModule():    events.append("setUpModule")
def tearDownModule(): events.append("tearDownModule")

class Lifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):    events.append("setUpClass")
    @classmethod
    def tearDownClass(cls): events.append("tearDownClass")
    def setUp(self):        events.append("setUp")
    def tearDown(self):     events.append("tearDown")
    def test_a(self):       events.append("test_a")
    def test_b(self):       events.append("test_b")

unittest.main(argv=["prog"], exit=False, verbosity=0)
assert events == ["setUpModule", "setUpClass",
                  "setUp", "test_a", "tearDown",
                  "setUp", "test_b", "tearDown",
                  "tearDownClass", "tearDownModule"], events
```

**Which hook when?**

* `setUp` — default choice. Cheap objects built fresh per test guarantee isolation.
* `setUpClass` — only for *expensive* and *immutable* shared resources (e.g. loading a big signal database). If a test mutates it, you have created a hidden dependency between tests.
* `tearDown` runs even when `setUp` passed and the test failed; it does **not** run if `setUp` itself raised. For cleanup that must happen regardless, register it with **`self.addCleanup(fn, *args)`** right after you allocate the resource — cleanups run in reverse order and also run if `setUp` fails part-way.

## 4.5 Assertions: say exactly what you mean

A specific assertion produces a specific failure message. Prefer the most specific one:

| Check | Method | Note |
|---|---|---|
| equality | `assertEqual(a, b)` | also compares lists, dicts, sets with a diff |
| inequality | `assertNotEqual(a, b)` | |
| floats | `assertAlmostEqual(a, b, places=7)` / `delta=` | **never** `assertEqual` on floats |
| boolean | `assertTrue(x)` / `assertFalse(x)` | weaker messages — use only for genuine booleans |
| identity / None | `assertIs`, `assertIsNone`, `assertIsNotNone` | `assertIs(result, BMSFault.NONE)` for enums |
| membership | `assertIn(a, container)` | |
| ordering | `assertGreater`, `assertLessEqual`, … | |
| type | `assertIsInstance(obj, cls)` | |
| exceptions | `assertRaises(Exc)` / `assertRaisesRegex(Exc, pattern)` | context-manager form preferred |
| collections | `assertCountEqual(a, b)` | same elements, any order |
| text | `assertRegex(text, pattern)` | |
| explicit | `self.fail("message")` | for unreachable branches |

**Why `assertEqual(a, b)` beats `assertTrue(a == b)`:** when it fails, the first prints both values; the second prints only `False is not true`.

### Exceptions
```python
# verified: python
import unittest
from autotest.sensors import wheel_speed_kmh

class T(unittest.TestCase):
    def test_zero_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            wheel_speed_kmh(10, 20, 2.0, 0)

    def test_message_names_the_problem(self):
        with self.assertRaisesRegex(ValueError, "invalid wheel speed"):
            wheel_speed_kmh(-1, 20, 2.0, 1.0)

r = unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
assert r.wasSuccessful()
```
Do **not** write `try: ... except ValueError: pass` — if the code raises *nothing*, the test silently passes. `assertRaises` fails in that case.

### Floating point
Binary floating point cannot represent most decimals, so `0.1 + 0.2 != 0.3`. Compare with a tolerance: `assertAlmostEqual(a, b, places=7)` rounds the *difference* to `places` decimals; `delta=0.01` states an absolute tolerance directly.

## 4.6 One test, many inputs: `subTest`

When the same check applies to several inputs, loop inside the test but wrap each iteration in `subTest`. A failing iteration is reported with its parameters and the loop **continues** (a bare loop would stop at the first failure):

```python
# verified: python
import unittest
from autotest.sensors import kmh_to_ms, ms_to_kmh

class T(unittest.TestCase):
    def test_round_trip(self):
        for kmh in (0, 1, 50, 130.5):
            with self.subTest(kmh=kmh):
                self.assertAlmostEqual(ms_to_kmh(kmh_to_ms(kmh)), kmh)

r = unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
assert r.wasSuccessful()
```

## 4.7 Skipping and known failures

Never delete or comment out a test you cannot make pass — make its status *visible*:

| Decorator | Meaning | Shown in the report as |
|---|---|---|
| `@unittest.skip("reason")` | not run | skipped (with reason) |
| `@unittest.skipIf(cond, "reason")` / `skipUnless` | conditional skip (platform, optional dependency) | skipped |
| `@unittest.expectedFailure` | a *known* bug: must fail | "expected failure"; becomes an **unexpected success** (a failure of the run) when someone fixes the bug, forcing cleanup |

## 4.8 Discovery and the command line

```bash
python -m unittest                                   # discover tests in ./ (files test*.py)
python -m unittest discover -s tests -p "test_*.py"  # explicit directory and pattern
python -m unittest tests.test_can                    # a module
python -m unittest tests.test_can.TestCRC            # a class
python -m unittest tests.test_can.TestCRC.test_check_value   # one method
python -m unittest -v                                # verbose, one line per test
python -m unittest -k crc                            # only tests whose name contains "crc"
python -m unittest -f                                # stop at first failure
python -m unittest -b                                # buffer stdout/stderr, show only for failures
```

The **exit code** is 0 only if everything passed — which is what a CI server looks at.

## 4.9 A first look at `unittest.mock`

`unittest.mock` (also in the standard library) replaces collaborators with controllable objects — central to Chapter 7. The essentials:

```python
# verified: python
from unittest import mock

adc = mock.Mock()
adc.read.return_value = 2048            # a stub: canned answer
assert adc.read() == 2048

adc.read.side_effect = [1, 2, OSError("bus error")]   # a sequence, then an exception
assert (adc.read(), adc.read()) == (1, 2)
try:
    adc.read()
except OSError:
    pass
assert adc.read.call_count == 4          # a spy: how often was it called?

with mock.patch("autotest.sensors.kmh_to_ms", return_value=123.0):
    from autotest import sensors
    assert sensors.kmh_to_ms(1) == 123.0  # replaced only inside the with-block
```

## 4.10 Strengths, limits, and when to choose it

| Strengths | Limits |
|---|---|
| in the standard library; stable for decades | boilerplate: classes, `self.assert*` zoo |
| explicit, familiar xUnit lifecycle | no parametrization (only `subTest`), no fixture injection |
| good fit for restricted environments and as a teaching tool | plain output for failures; fewer plugins |

**Choose `unittest`** when you must avoid third-party dependencies or integrate with a house xUnit style. **Choose `pytest`** (next chapter) for new projects. You can mix: pytest happily runs `TestCase` classes, so a codebase can migrate gradually.

## Check your understanding

1. A test class creates a battery object in `setUpClass` and one test charges it. What can go wrong in the other tests?
2. Why does `with self.assertRaises(ValueError):` appear in every serious test suite rather than `try/except`?
3. What is the difference between a test **failure** and a test **error**?
4. You have a known bug you cannot fix this sprint. Compare `@unittest.skip` and `@unittest.expectedFailure`. Which is better and why?

<!--ANSWERS-->
1. The charge changes the shared object; any test running afterwards sees a different SOC, so results depend on execution order — hidden coupling. Build the object in `setUp` instead.
2. With `try/except … pass`, a function that raises nothing still passes. `assertRaises` fails if no exception is raised, so the test genuinely verifies the behaviour.
3. A failure is an assertion that was violated (the code disagreed with the oracle). An error is any other exception — the test or the code crashed in an unanticipated way.
4. `expectedFailure` keeps *running* the test and reports an unexpected success when the bug is fixed, forcing cleanup. `skip` hides it entirely and the test can rot unnoticed.
