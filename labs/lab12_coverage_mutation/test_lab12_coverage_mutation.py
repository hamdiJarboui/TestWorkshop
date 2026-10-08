"""Lab 12 - coverage is necessary, not sufficient: mutation analysis as a test of the tests.

These tests drive tools/mini_mutate.py (a subprocess per mutant, so they are marked slow).
"""
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from autotest.bms import max_charge_current

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.slow


def mutation_score(tests: str) -> tuple[int, int, str]:
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "mini_mutate.py"),
         "--target", "src/autotest/bms.py", "--function", "max_charge_current", "--tests", tests],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
    ).stdout
    line = next(l for l in out.splitlines() if l.startswith("mutation score"))
    killed, total = line.split(":")[1].split("=")[0].strip().split("/")
    return int(killed), int(total), out


def test_the_strong_suite_from_lab3_kills_all_non_equivalent_mutants():
    killed, total, out = mutation_score("labs/lab03_black_box/test_lab03_black_box.py")
    survivors = total - killed
    # The three survivors are EQUIVALENT mutants - they change the code but not its behaviour:
    #   `soc >= 100` -> `soc > 100` / `soc >= 101`, and `soc > 80` -> `soc >= 80`.
    # The taper formula already yields 0 A at 100 % and the full limit at 80 %, so the explicit
    # `soc >= 100` guard is REDUNDANT code - mutation testing just told us so.
    # No test can kill an equivalent mutant; recognising them is a human skill.
    assert survivors <= 3, out


def test_the_weak_suite_has_full_coverage_but_a_poor_mutation_score():
    killed, total, out = mutation_score("labs/lab12_coverage_mutation/weak_suite.py")
    assert killed / total < 0.6, out


def test_coverage_report_for_bms_is_complete_for_the_weak_suite(tmp_path):
    report = tmp_path / "cov.json"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "labs/lab12_coverage_mutation/weak_suite.py", "-q",
         "--cov=autotest.bms", "--cov-branch", f"--cov-report=json:{report}", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, r.stdout
    files = json.loads(report.read_text(encoding="utf-8"))["files"]
    # report keys use the OS path separator, so match on the normalised tail
    data = next(v for k, v in files.items() if k.replace("\\", "/").endswith("src/autotest/bms.py"))
    lines, first = inspect.getsourcelines(max_charge_current)
    inside = set(range(first, first + len(lines)))
    # The weak suite never touches the BatteryManagementSystem class (expected). What matters is
    # that NOTHING inside max_charge_current is missing - neither lines nor branches.
    assert not inside & set(data["missing_lines"]), data["missing_lines"]
    assert not inside & {a for a, _ in data["missing_branches"]}, data["missing_branches"]
