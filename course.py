#!/usr/bin/env python3
"""One friendly entry point for the whole course - works on Windows, macOS and Linux, no `make` needed.

    python course.py doctor          check your setup (start here!)
    python course.py labs            list the labs and your exercise progress
    python course.py lab 3           run the worked examples of Lab 3 (read them first)
    python course.py exercise 3      run YOUR exercises of Lab 3
    python course.py progress        how many exercise tests pass, per lab
    python course.py test            the fast everyday test run
    python course.py smoke           the quickest sanity check
    python course.py coverage        coverage report (Lab 12)
    python course.py mutation        mutation score of the Lab 3 suite (Lab 12)
    python course.py capstone        grade your capstone test suite
    python course.py check-course    run every code example in the lecture chapters
    python course.py pdf             rebuild the PDF books (needs pandoc + Chromium)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = {**os.environ, "PYTHONPATH": f"{ROOT / 'src'}{os.pathsep}{ROOT}"}   # works even without `pip install -e .`


def run(*args: str, quiet: bool = False) -> subprocess.CompletedProcess:
    cmd = [sys.executable, *args]
    return subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=quiet, text=True, encoding="utf-8", errors="replace")


def pytest(*args: str, quiet: bool = False) -> subprocess.CompletedProcess:
    return run("-m", "pytest", "-p", "no:cacheprovider", *args, quiet=quiet)


def lab_dirs() -> list[Path]:
    return sorted(p for p in (ROOT / "labs").iterdir() if p.is_dir() and re.match(r"lab\d\d_", p.name))


def lab_dir(n: int) -> Path:
    for p in lab_dirs():
        if p.name.startswith(f"lab{n:02d}_"):
            return p
    sys.exit(f"There is no Lab {n}. Run `python course.py labs` to see the list.")


def lab_title(d: Path) -> str:
    first = (d / "README.md").read_text(encoding="utf-8").splitlines()[0]
    return re.sub(r"^#\s*Lab \d+\s*[—-]\s*", "", first).replace("`", "")


def exercise_file(n: int) -> Path | None:
    files = sorted(lab_dir(n).glob("exercise_*.py"))
    return files[0] if files else None


def exercise_score(path: Path) -> tuple[int, int]:
    """(passed, total) for one exercise file."""
    out = pytest(str(path), "-q", "--tb=no", "-rN", "-o", "addopts=", "--import-mode=importlib", quiet=True).stdout
    passed = sum(int(m) for m in re.findall(r"(\d+) passed", out))
    failed = sum(int(m) for m in re.findall(r"(\d+) (?:failed|error)", out))
    return passed, passed + failed


# ------------------------------------------------------------------ commands
def cmd_doctor() -> int:
    ok = True

    def check(label: str, good: bool, fix: str = "") -> None:
        nonlocal ok
        print(f"  [{'OK' if good else '!!'}] {label}" + ("" if good else f"\n        -> {fix}"))
        ok &= good

    print("Checking your setup...\n")
    check(f"Python {sys.version.split()[0]} (need 3.10 or newer)", sys.version_info >= (3, 10),
          "install a newer Python from python.org")
    for mod, pkg in (("pytest", "pytest"), ("hypothesis", "hypothesis"), ("pytest_cov", "pytest-cov")):
        try:
            __import__(mod)
            check(f"{pkg} is installed", True)
        except ImportError:
            check(f"{pkg} is installed", False, "run:  pip install -r requirements.txt")
    r = run("-c", "import autotest.can", quiet=True)
    check("the course library `autotest` can be imported", r.returncode == 0, "run this from the repository folder")
    if ok:
        r = pytest("labs/lab00_setup/test_lab00_first_test.py", "-q", "--tb=short", quiet=True)
        check("your first tests run (Lab 0)", r.returncode == 0, "run:  python course.py lab 0   and read the error")
        if r.returncode:
            print(r.stdout[-1500:])
    print("\n" + ("Everything is ready.  Next: open labs/lab00_setup/README.md   (or run: python course.py labs)"
                  if ok else "Fix the items marked [!!] above, then run `python course.py doctor` again."))
    return 0 if ok else 1


def cmd_labs() -> int:
    print(f"{'Lab':<5}{'Title':<58}{'Exercises'}")
    for d in lab_dirs():
        n = int(d.name[3:5])
        ex = exercise_file(n)
        score = ""
        if ex:
            p, t = exercise_score(ex)
            score = f"{p}/{t} {'done' if p == t and t else ''}"
        print(f"{n:<5}{lab_title(d)[:56]:<58}{score}")
    print("\nWork on a lab:  python course.py lab N   (worked examples)   then   python course.py exercise N")
    return 0


def cmd_lab(n: int) -> int:
    print(f"Lab {n}: worked examples (read the code in {lab_dir(n).relative_to(ROOT)}/test_*.py)\n")
    return pytest(str(lab_dir(n)), "-v", "--no-header", "--tb=short", "-o", "addopts=-ra --strict-markers --import-mode=importlib",
                  "--ignore-glob=*exercise_*").returncode


def cmd_exercise(n: int) -> int:
    ex = exercise_file(n)
    if not ex:
        sys.exit(f"Lab {n} has no exercise file.")
    print(f"Lab {n}: your exercises ({ex.relative_to(ROOT)})\n"
          "A test that says 'TODO' is not started yet: open the file, read its docstring, delete the todo(...) line,\n"
          "write your code, run this command again.\n")
    code = pytest(str(ex), "-v", "--no-header", "--tb=short", "-o", "addopts=--strict-markers --import-mode=importlib").returncode
    passed, total = exercise_score(ex)
    print(f"\nLab {n} progress: {passed}/{total} tests pass" + ("  - lab complete!" if passed == total else "  - keep going, one test at a time."))
    return code


def cmd_progress() -> int:
    done = total = 0
    for d in lab_dirs():
        n = int(d.name[3:5])
        ex = exercise_file(n)
        if not ex:
            continue
        p, t = exercise_score(ex)
        done, total = done + p, total + t
        bar = "#" * p + "." * (t - p)
        print(f"Lab {n:>2}  [{bar}]  {p}/{t}")
    print(f"\n{done}/{total} exercise tests pass" + ("  - well done!" if done == total and total else ""))
    return 0


COMMANDS_SIMPLE = {
    "test": lambda: pytest("-m", "not slow and not performance", "-q").returncode,
    "smoke": lambda: pytest("-m", "smoke", "-q").returncode,
    "coverage": lambda: pytest("-m", "not slow", "--cov=autotest", "--cov-branch", "--cov-report=term-missing", "-q").returncode,
    "mutation": lambda: run("tools/mini_mutate.py", "--target", "src/autotest/bms.py", "--function", "max_charge_current",
                            "--tests", "labs/lab03_black_box/test_lab03_black_box.py").returncode,
    "capstone": lambda: run("capstone/grade.py", *sys.argv[2:]).returncode,
    "check-course": lambda: run("tools/check_course_code.py").returncode,
    "pdf": lambda: run("tools/build_pdf.py").returncode,
}


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "doctor":
        return cmd_doctor()
    if cmd == "labs":
        return cmd_labs()
    if cmd == "progress":
        return cmd_progress()
    if cmd in ("lab", "exercise"):
        if len(rest) != 1 or not rest[0].isdigit():
            sys.exit(f"usage: python course.py {cmd} N      (N = lab number, e.g. 3)")
        return (cmd_lab if cmd == "lab" else cmd_exercise)(int(rest[0]))
    if cmd in COMMANDS_SIMPLE:
        return COMMANDS_SIMPLE[cmd]()
    print(f"Unknown command {cmd!r}.\n{__doc__}")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:        # e.g. `python course.py labs | head`
        sys.exit(0)
