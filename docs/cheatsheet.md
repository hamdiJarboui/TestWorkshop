# unittest ↔ pytest cheat sheet

| Task | `unittest` | `pytest` |
|---|---|---|
| Test discovery | `class X(unittest.TestCase)`, methods `test_*` | any function `test_*` (classes optional, no base class) |
| Assertion | `self.assertEqual(a, b)` and ~30 other `assertXxx` | `assert a == b` (introspected failure message) |
| Floats | `assertAlmostEqual(a, b, places=7)` | `assert a == pytest.approx(b, rel=1e-6, abs=1e-12)` |
| Exception | `with self.assertRaises(E):` / `assertRaisesRegex` | `with pytest.raises(E, match="re") as info:` |
| Setup / teardown | `setUp`, `tearDown`, `setUpClass`, `tearDownClass` | fixtures with `yield`; scopes `function/class/module/session` |
| Many inputs | `with self.subTest(x=x):` in a loop | `@pytest.mark.parametrize("x", [...], ids=[...])` |
| Skip | `@unittest.skip`, `skipIf`, `skipUnless` | `@pytest.mark.skip`, `skipif(cond, reason=...)`, `pytest.skip()` |
| Known failure | `@unittest.expectedFailure` | `@pytest.mark.xfail(reason=..., strict=True)` |
| Temp files | `tempfile.TemporaryDirectory` | `tmp_path`, `tmp_path_factory` |
| Patch | `mock.patch("pkg.mod.name")` | `monkeypatch.setattr/setenv/delattr` (or `mock.patch`) |
| Capture output | `contextlib.redirect_stdout` | `capsys`, `caplog` |
| Run | `python -m unittest discover -v` | `pytest -v` (also runs unittest tests) |

## Everyday pytest commands

```bash
pytest -x                    # stop at first failure
pytest --lf                  # re-run only last failures
pytest -k "cruise and not hill"      # select by name expression
pytest -m "smoke"            # select by marker;  -m "not slow and not performance"
pytest path/file.py::test_name[param-id]   # one test
pytest -vv --tb=short        # verbose, compact tracebacks
pytest --durations=10        # slowest tests
pytest -rs                   # why were tests skipped?
pytest --pdb                 # debugger at failure
pytest --cov=autotest --cov-branch --cov-report=term-missing
pytest --junitxml=report.xml
pytest --hil / --update-golden / --req-report      # this course's options
```

## Choosing the right double

| Double | Purpose | Example in this course |
|---|---|---|
| Dummy | fills a parameter, never used | listener subscribed to another id |
| Stub | returns canned answers | `StubADC(0)` → short-to-ground |
| Fake | simplified working implementation | `FakeClock`, `VirtualCANBus`, `SineWaveADC` |
| Spy | real object + call recording | `SpyADC.calls`, `SpyListener.frames` |
| Mock | verifies interactions | `Mock(spec=DiagnosticManager).report.assert_called_with(...)` |

Prefer **state/outcome** assertions over interaction assertions; mock only what is slow, non-deterministic or hardware.

## Test-design checklist

* One reason to fail per test; name says *what* and *under which condition*.
* Arrange – Act – Assert (or Given – When – Then).
* Boundaries: on, just below, just above. Empty, one, many. Zero, negative, NaN, huge.
* Determinism: inject clocks and RNG seeds; no `sleep`, no network, no shared state.
* Every defect fixed gets a regression test **first** (red → green).
* Tests are code: review them, refactor them, delete the ones that no longer protect anything.

## The course runner

```bash
python course.py doctor | labs | progress | test | smoke | coverage | mutation | capstone | check-course | pdf
python course.py lab N          # worked examples of lab N (verbose)
python course.py exercise N     # your exercises of lab N
```
