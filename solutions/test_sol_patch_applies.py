"""Guard: the instructor patch for Lab 8 must keep applying to the current code.

`solutions/bms_nan_fix.patch` fixes BUG-201/202 and removes the two strict-xfail markers. It was once
silently broken by an unrelated edit to bms.py - this test makes that impossible to miss.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("patch") is None, reason="the `patch` tool is not installed")
def test_bms_nan_fix_patch_applies_cleanly(tmp_path):
    for folder in ("src", "labs"):
        shutil.copytree(ROOT / folder, tmp_path / folder, ignore=shutil.ignore_patterns("__pycache__", "golden", "data"))
    patch_file = str(ROOT / "solutions" / "bms_nan_fix.patch")

    def dry_run(*extra):
        return subprocess.run(["patch", "-p1", "--dry-run", *extra, "-i", patch_file], cwd=tmp_path,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    result = dry_run()
    if result.returncode != 0 and dry_run("-R").returncode == 0:
        pytest.skip("the patch is already applied to this tree (you fixed BUG-201/202)")
    assert result.returncode == 0, f"bms_nan_fix.patch no longer applies - regenerate it:\n{result.stdout}{result.stderr}"
