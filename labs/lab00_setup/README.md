# Lab 0 — Setup and your very first tests

**Duration:** 30–45 min · **Goal:** a working environment, and a feel for how every lab works.

> No lecture precedes this lab. If you can run `python course.py doctor` successfully, you are ready for Chapter 1.

## 1. Install (once)

You need **Python 3.10 or newer** (check with `python --version`; on some systems the command is `python3`).

```bash
# in the repository folder
python -m venv .venv                      # a private Python environment for this course
source .venv/bin/activate                 # Windows:  .venv\Scripts\activate
pip install -r requirements.txt           # pytest, coverage, hypothesis + the course library
python course.py doctor                   # checks everything and runs your first tests
```

`doctor` prints `[OK]` for each check, or `[!!]` with the exact fix. Nothing else in this course needs `make`, `PYTHONPATH` or a special IDE.

## 2. How the course is organised

| What | Where | You do |
|---|---|---|
| **Lectures** | the PDF book, or `course/lecture_NN_*.md` | read first (30–60 min each) |
| **Worked examples** | `labs/labNN_*/test_*.py` | run them, read them, *break* them |
| **Exercises** | `labs/labNN_*/exercise_labNN.py` | write the missing tests |
| **Code under test** | `src/autotest/` | read it *after* designing tests from the spec |

The commands you will use all the time:

```bash
python course.py labs            # list of labs + your progress
python course.py lab 3           # run the worked examples of Lab 3
python course.py exercise 3      # run YOUR exercises of Lab 3
python course.py progress        # progress bars for every lab
```

## 3. Your first test, step by step

A test is a function that calls the code and **asserts** what must be true. Open
`test_lab00_first_test.py` — it contains three small tests of a real function, `kmh_to_ms` (km/h → m/s):

```python
def test_36_kmh_is_10_metres_per_second():
    assert kmh_to_ms(36) == pytest.approx(10.0)
```

Run it:

```bash
python course.py lab 0
```

You will see `PASSED` for each test. Now do the most important thing you will do all course — **break it**:

1. Open `src/autotest/sensors.py` and change `kmh / 3.6` to `kmh / 3.7` in `kmh_to_ms`.
2. Run `python course.py lab 0` again. Tests **fail**, and pytest shows the two values it compared (look for the `E` lines).
3. Read the failure message, then change the code back.

A failing test with a clear message is the point of testing: it *tells you what broke*.

## 4. How exercises work

Every exercise test starts with a `todo(...)` line, so it **fails** until you start:

```python
def test_72_kmh_is_20_metres_per_second():
    todo("call kmh_to_ms(72) and assert the result is 20")     # <- delete this line when you start
```

1. Read the docstring (it has the goal and **hints**; read them one at a time).
2. **Delete the `todo(...)` line** and write your test.
3. Run `python course.py exercise 0`. When all tests pass, run `python course.py progress`.

If you get stuck: read the hints, re-read the lecture, run the worked example of the same lab, and only then ask.

## 5. Exercise (in `exercise_lab00.py`)

Write the two tests described there. They take five minutes and use only `assert` and `pytest.raises`.

## Debrief questions
* What does `pytest.approx` do, and why not `==` for floats?
* When a test fails, which two numbers does pytest show you?
* Why is it useful to *break the code on purpose* and watch a test fail?
