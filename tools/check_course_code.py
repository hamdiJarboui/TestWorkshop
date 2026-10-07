#!/usr/bin/env python3
"""Execute the code examples embedded in the lecture chapters (course/*.md).

A fenced python block is checked when its FIRST line is one of
    # verified: python    -> run with plain python (must not raise)
    # verified: pytest    -> saved as a test module and run with pytest (must pass)
Blocks without a marker are illustrative and are not executed.

    python tools/check_course_code.py            # all chapters
    python tools/check_course_code.py course/lecture_05_pytest.md
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^```python\n(# verified: (python|pytest)\n.*?)^```", re.S | re.M)


def blocks(path: Path):
    for m in FENCE.finditer(path.read_text(encoding="utf-8")):
        line = path.read_text(encoding="utf-8")[: m.start()].count("\n") + 2
        yield line, m.group(2), m.group(1)


def main() -> int:
    files = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "course").glob("*.md"))
    env = {**os.environ, "PYTHONPATH": f"{ROOT / 'src'}{os.pathsep}{ROOT}", "PYTHONDONTWRITEBYTECODE": "1"}
    total = failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            for line, kind, code in blocks(f):
                total += 1
                name = f"{f.stem}_L{line}"
                script = Path(tmp) / (f"test_{name}.py" if kind == "pytest" else f"{name}.py")
                script.write_text(code, encoding="utf-8")
                cmd = ([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--rootdir", tmp, str(script)]
                       if kind == "pytest" else [sys.executable, str(script)])
                r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, env=env)
                if r.returncode:
                    failed += 1
                    print(f"FAIL {f.name}:{line} ({kind})\n{(r.stdout + r.stderr)[-1500:]}")
    print(f"{total - failed}/{total} verified code examples pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
