#!/usr/bin/env python3
"""Build the course PDFs from the repository's Markdown and source files.

    python tools/build_pdf.py            # writes pdf/*.pdf

Needs: pandoc and a Chromium/Chrome binary (set CHROME=/path/to/chrome if not auto-detected).
Two editions are produced:
  * Course Book        - for learners: overview, 13 labs (+ worked source + exercises), capstone, code under test
  * Instructor Edition - Course Book + course design, instructor guide, solutions, grader
"""
from __future__ import annotations

import datetime
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pdf"
TITLE = "Testing with Python"
SUBTITLE = "unittest, pytest and automotive software — a hands-on course in 13 labs"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def clean(md: str) -> str:
    md = re.sub(r"\[([^\]]+)\]\((?!https?://|#)[^)]*\)", r"\1", md)   # relative links are dead in a PDF
    md = md.replace("<details>", "<details open>")                    # print expanded
    return md


def source(rel: str, lang: str = "python") -> str:
    body = read(rel).rstrip("\n")
    return f'\n\n<div class="filepath">{rel}</div>\n\n````{lang}\n{body}\n````\n\n'


def lab_dirs():
    return sorted(p for p in (ROOT / "labs").iterdir() if p.is_dir() and p.name.startswith("lab"))


def chapter_lab(d: Path) -> str:
    rel = d.relative_to(ROOT)
    parts = [clean(read(f"{rel}/README.md")).rstrip() + "\n"]
    tests = sorted(d.glob("test_*.py"))
    extras = sorted(p for p in d.glob("*.py") if not p.name.startswith(("test_", "exercise_")))
    exercises = sorted(d.glob("exercise_*.py"))
    for group, heading in ((tests, "Worked example — source"), (extras, "Additional file"), (exercises, "Exercise skeleton — source")):
        for p in group:
            parts.append(f"\n## {heading}\n" + source(str(p.relative_to(ROOT))))
    return "\n".join(parts)


def cover(kicker: str) -> str:
    today = datetime.date.today().strftime("%d %B %Y")
    return f"""<section class="cover">
<div class="kicker">{kicker}</div>
<h1>{TITLE}</h1>
<div class="sub">{SUBTITLE}</div>
<div class="meta">Unit · Integration · System · Property-based · Robustness · Regression · Performance · Simulation · Mutation · Acceptance<br>
Python 3.10+ · pytest · unittest · Hypothesis · built {today}</div>
</section>"""


def build_markdown(instructor: bool) -> str:
    md = []
    overview = clean(read("README.md")).replace(
        "# Testing with Python — unittest, pytest & Automotive Software", "# About this course", 1)
    if not instructor:   # instructor-only material is not part of the learner edition
        overview = overview.replace("; see COURSE_DESIGN.md)", ")")
        overview = "\n".join(l for l in overview.splitlines()
                             if "instructor_guide.md" not in l and "COURSE_DESIGN.md" not in l)
    md.append(overview)
    for d in lab_dirs():
        md.append(chapter_lab(d))
    md.append(clean(read("capstone/README.md")))
    md.append("\n## Starter test suite — source\n" + source("capstone/test_tpms_student.py"))
    md.append("\n# Appendix A — Cheat sheet\n" + clean(read("docs/cheatsheet.md")).split("\n", 1)[1])
    md.append("\n# Appendix B — Code under test\n\nThe complete `src/autotest` library that every lab tests. "
              "Read it only after designing tests from the specifications — that is the point of Lab 3.\n")
    for p in sorted((ROOT / "src/autotest").glob("*.py")):
        md.append(f"\n## {p.name}\n" + source(str(p.relative_to(ROOT))))
    md.append("\n# Appendix C — Course tooling\n\n## Shared fixtures and options\n" + source("conftest.py"))
    md.append("\n## Mutation tester (Lab 12)\n" + source("tools/mini_mutate.py"))
    md.append("\n## Requirements used for traceability (Lab 13)\n" + source("docs/requirements.csv", "text"))
    if instructor:
        md.append(clean(read("COURSE_DESIGN.md")))
        md.append(clean(read("docs/instructor_guide.md")))
        md.append("\n# Appendix D — Instructor solutions\n\n" + clean(read("solutions/README.md")).split("\n", 1)[1])
        for p in sorted((ROOT / "solutions").glob("*.py")):
            if p.name == "__init__.py":
                continue
            md.append(f"\n## {p.name}\n" + source(str(p.relative_to(ROOT))))
        md.append("\n## bms_nan_fix.patch (Lab 8)\n" + source("solutions/bms_nan_fix.patch", "diff"))
        md.append("\n## Capstone grader\n" + source("capstone/grade.py"))
    return "\n\n".join(md)


def find_chrome() -> str:
    cands = [os.environ.get("CHROME", "")] + glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome") + [
        shutil.which(n) or "" for n in ("google-chrome", "chromium", "chromium-browser", "chrome")]
    for c in cands:
        if c and Path(c).exists():
            return c
    sys.exit("No Chrome/Chromium found: set CHROME=/path/to/chrome")


def render(name: str, kicker: str, instructor: bool) -> Path:
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "book.md").write_text(build_markdown(instructor), encoding="utf-8")
        (tmp / "cover.html").write_text(cover(kicker), encoding="utf-8")
        html = tmp / "book.html"
        subprocess.run([
            "pandoc", str(tmp / "book.md"), "-f", "gfm+attributes", "-t", "html5", "--standalone",
            "--template", str(ROOT / "tools/pdf/template.html"), "--toc", "--toc-depth=1",
            "--highlight-style=pygments", "--metadata", f"pagetitle={TITLE}",
            "-V", f"styles={(ROOT / 'tools/pdf/style.css').read_text()}",
            "--include-before-body", str(tmp / "cover.html"), "-o", str(html)], check=True)
        pdf = OUT / name
        subprocess.run([find_chrome(), "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", html.as_uri()], check=True, capture_output=True)
    return pdf


if __name__ == "__main__":
    for fname, kicker, inst in (("Testing-with-Python-Course-Book.pdf", "Course Book", False),
                                ("Testing-with-Python-Instructor-Edition.pdf", "Instructor Edition", True)):
        p = render(fname, kicker, inst)
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size / 1024:.0f} KiB")
