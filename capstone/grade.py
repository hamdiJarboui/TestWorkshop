#!/usr/bin/env python3
"""Capstone grader: how many hidden defects does YOUR test suite catch?

    python capstone/grade.py                                  # grades capstone/test_tpms_student.py
    python capstone/grade.py --tests solutions/test_sol_capstone_tpms.py

For each defect ("mutant") the grader injects ONE bug into src/autotest/tpms.py in a scratch
copy of the project and runs your tests. You catch a defect when at least one test FAILS.
The reference implementation must pass your tests first (no false alarms allowed).
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from mini_mutate import run_tests  # noqa: E402

TARGET = "src/autotest/tpms.py"

# (id, symptom shown to students, exact source text, replacement)
DEFECTS = [
    ("D01", "classification wrong exactly at the CRITICAL/LOW threshold", "if p20 < 0.6 * nominal:", "if p20 <= 0.6 * nominal:"),
    ("D02", "classification wrong exactly at the LOW/OK threshold", "if p20 < 0.8 * nominal:", "if p20 <= 0.8 * nominal:"),
    ("D03", "classification wrong exactly at the OK/HIGH threshold", "if p20 <= 1.3 * nominal:", "if p20 < 1.3 * nominal:"),
    ("D04", "temperature compensation is slightly off", "273.15 + temp_c", "273.0 + temp_c"),
    ("D05", "sensor range: upper pressure limit", "not 0 <= kpa <= 700", "not 0 <= kpa < 700"),
    ("D06", "sensor range: lower pressure limit", "not 0 <= kpa <= 700", "not 0 < kpa <= 700"),
    ("D07", "sensor range: lower temperature limit", "-40 <= temp_c <= 125", "-40 < temp_c <= 125"),
    ("D08", "sensor range: upper temperature limit", "-40 <= temp_c <= 125", "-40 <= temp_c < 125"),
    ("D09", "sensor id validation accepts too much", "{8}", "{8,}"),
    ("D10", "sensor id is not normalised", "return sensor_id.upper()", "return sensor_id"),
    ("D11", "leak alarm threshold off by one step", "highest - kpa >= self.DROP_KPA", "highest - kpa > self.DROP_KPA"),
    ("D12", "leak window edge handled wrongly", "t - self._samples[0][0] > self.WINDOW_S", "t - self._samples[0][0] >= self.WINDOW_S"),
    ("D13", "leak detector looks at the wrong extreme", "highest = max(", "highest = min("),
    ("D14", "default nominal pressure changed", "NOMINAL_KPA = 230.0", "NOMINAL_KPA = 220.0"),
    ("D15", "leak window length changed", "WINDOW_S = 60.0", "WINDOW_S = 30.0"),
    ("D16", "over-pressure is never reported", "return TyreStatus.HIGH", "return TyreStatus.OK"),
    ("D17", "leak detector forgets nothing (old samples never expire)", "while self._samples and t - self._samples[0][0] > self.WINDOW_S:", "while False:"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", default="capstone/test_tpms_student.py")
    ap.add_argument("--min-score", type=float, default=0.0, help="exit 1 below this percentage")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "proj"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".pytest_cache", ".hypothesis", "htmlcov", ".coverage"))
        target = work / TARGET
        original = target.read_text()
        if not run_tests(work, [args.tests], 120):
            print("Your tests FAIL on the correct implementation - fix your tests first.")
            return 2
        caught = 0
        for did, symptom, old, new in DEFECTS:
            assert old in original, f"grader out of date: {did}"
            target.write_text(original.replace(old, new, 1))
            killed = not run_tests(work, [args.tests], 120)
            caught += killed
            print(f"  {did} {'caught  ' if killed else 'MISSED  '} {symptom if not killed else ''}")
        target.write_text(original)
    score = 100 * caught / len(DEFECTS)
    print(f"\ndefects caught: {caught}/{len(DEFECTS)} = {score:.0f} %")
    return 0 if score >= args.min_score else 1


if __name__ == "__main__":
    sys.exit(main())
