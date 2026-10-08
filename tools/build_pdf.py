#!/usr/bin/env python3
"""Build the course PDFs from the repository's Markdown and source files.

    python tools/build_pdf.py            # writes pdf/*.pdf

Needs: pandoc and a Chromium/Chrome binary (set CHROME=/path/to/chrome if not auto-detected).

Book structure (heading levels:  H1 = part, H2 = chapter / lab, H3+ = sections)
    Start here · I Foundations · II The tools · III Test design & isolation · IV Integration & system ·
    V Finding the unexpected · VI Change, speed & simulation · VII Adequacy, evidence & delivery ·
    VIII Capstone · Appendices (glossary, reading, cheat sheet, code under test, tooling, answers)
Each lab is preceded by its lecture chapter. Two editions:
  * Course Book        - for learners
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
SUBTITLE = "unittest, pytest and automotive software — lectures, labs and a capstone"

# (part title, [("lecture", chapter-number, file) | ("lab", n) | ("file", title, path)])
PARTS = [
    ("Part I — Foundations", [("lecture", 1, "lecture_01_why_we_test"), ("lecture", 2, "lecture_02_testing_landscape"),
                               ("lecture", 3, "lecture_03_automotive_primer")]),
    ("Part II — The tools: unittest and pytest", [("lab", 0), ("lecture", 4, "lecture_04_unittest"), ("lab", 1),
                                                 ("lecture", 5, "lecture_05_pytest"), ("lab", 2)]),
    ("Part III — Test design and isolation", [("lecture", 6, "lecture_06_test_design"), ("lab", 3),
                                              ("lecture", 7, "lecture_07_test_doubles"), ("lab", 4)]),
    ("Part IV — Integration and system testing", [("lecture", 8, "lecture_08_integration_testing"), ("lab", 5),
                                                  ("lecture", 9, "lecture_09_state_and_system_testing"), ("lab", 6)]),
    ("Part V — Finding the unexpected", [("lecture", 10, "lecture_10_property_based_and_fuzz"), ("lab", 7),
                                         ("lecture", 11, "lecture_11_robustness_and_fault_injection"), ("lab", 8)]),
    ("Part VI — Change, speed and simulation", [("lecture", 12, "lecture_12_regression_testing"), ("lab", 9),
                                                ("lecture", 13, "lecture_13_performance_and_realtime"), ("lab", 10),
                                                ("lecture", 14, "lecture_14_simulation_and_sil"), ("lab", 11)]),
    ("Part VII — Adequacy, evidence and delivery", [("lecture", 15, "lecture_15_test_adequacy"), ("lab", 12),
                                                    ("lecture", 16, "lecture_16_requirements_traceability_ci"), ("lab", 13)]),
    ("Part VIII — Capstone", [("lecture", 17, "lecture_17_putting_it_together"), ("capstone",)]),
]
ANSWERS_MARK = "<!--ANSWERS-->"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def clean(md: str) -> str:
    md = re.sub(r"\[([^\]]+)\]\((?!https?://|#)[^)]*\)", r"\1", md)   # relative links are dead in a PDF
    md = md.replace("<details>", "<details open>")                    # print expanded
    md = re.sub(r"^> \*\*Read first:\*\*.*\n?", "", md, flags=re.M)   # redundant: the lecture precedes the lab
    return md


def shift(md: str, n: int = 1) -> str:
    """Demote every Markdown heading by n levels, ignoring fenced code blocks."""
    out, fence = [], None
    for line in md.split("\n"):
        m = re.match(r"^(`{3,}|~{3,})", line)
        if m:
            fence = None if fence == m.group(1)[0] else (fence or m.group(1)[0])
        if fence is None and re.match(r"^#{1,5} ", line):
            line = "#" * n + line
        out.append(line)
    return "\n".join(out)


def source(rel: str, lang: str = "python") -> str:
    body = read(rel).rstrip("\n")
    return f'\n\n<div class="filepath">{rel}</div>\n\n````{lang}\n{body}\n````\n\n'


def retitle(md: str, new_title: str) -> str:
    return re.sub(r"^# .*$", f"# {new_title}", md, count=1, flags=re.M)


def lab_dir(n: int) -> Path:
    return next(p for p in (ROOT / "labs").iterdir() if p.name.startswith(f"lab{n:02d}_"))


def chapter_lab(n: int) -> str:
    d = lab_dir(n)
    rel = d.relative_to(ROOT)
    parts = [clean(read(f"{rel}/README.md")).rstrip() + "\n"]
    tests = sorted(d.glob("test_*.py"))
    extras = sorted(p for p in d.glob("*.py") if not p.name.startswith(("test_", "exercise_")))
    exercises = sorted(d.glob("exercise_*.py"))
    for group, heading in ((tests, "Worked example — source"), (extras, "Additional file"), (exercises, "Exercise skeleton — source")):
        for p in group:
            parts.append(f"\n## {heading}\n" + source(str(p.relative_to(ROOT))))
    return shift("\n".join(parts))


def chapter_lecture(num: int, stem: str) -> tuple[str, str, str]:
    """Return (chapter markdown, answers markdown, title)."""
    raw = read(f"course/{stem}.md")
    body, _, answers = raw.partition(ANSWERS_MARK)
    body = re.sub(r"^# verified: (python|pytest)\n", "", body, flags=re.M)   # checker tags are not for readers
    title = re.search(r"^# (.*)$", body, re.M).group(1)
    md = shift(retitle(body, f"Chapter {num} — {title}").rstrip() + "\n")
    ans = f"\n### Chapter {num} — {title}\n\n{answers.strip()}\n" if answers.strip() else ""
    return md, ans, title


def part_heading(title: str) -> str:
    return f"\n\n# {title}\n\n"


def cover(kicker: str) -> str:
    today = datetime.date.today().strftime("%d %B %Y")
    return f"""<section class="cover">
<div class="kicker">{kicker}</div>
<h1>{TITLE}</h1>
<div class="sub">{SUBTITLE}</div>
<div class="meta">17 lecture chapters · Lab 0 + 13 labs · capstone · glossary · self-check answers<br>
Unit · Integration · System · Property-based · Robustness · Regression · Performance · Simulation · Mutation · Acceptance<br>
Python 3.10+ · pytest · unittest · Hypothesis · built {today}</div>
</section>"""


def build_markdown(instructor: bool) -> str:
    md = [part_heading("Start here")]
    overview = clean(read("README.md")).replace(
        "# Testing with Python — unittest, pytest & Automotive Software", "# About this course", 1)
    if not instructor:   # instructor-only material is not part of the learner edition
        overview = overview.replace("; see COURSE_DESIGN.md)", ")")
        overview = "\n".join(l for l in overview.splitlines()
                             if "instructor_guide.md" not in l and "COURSE_DESIGN.md" not in l)
    md.append(shift(overview))
    answers = []
    for title, items in PARTS:
        md.append(part_heading(title))
        for item in items:
            kind = item[0]
            if kind == "lecture":
                chapter, ans, _ = chapter_lecture(item[1], item[2])
                md.append(chapter)
                answers.append(ans)
            elif kind == "lab":
                md.append(chapter_lab(item[1]))
            elif kind == "capstone":
                md.append(shift(clean(read("capstone/README.md"))))
                md.append(shift("\n## Starter test suite — source\n" + source("capstone/test_tpms_student.py")))
    md.append(part_heading("Appendices"))
    md.append(shift(clean(read("course/appendix_glossary.md")).replace("# Glossary", "# Appendix A — Glossary", 1)))
    md.append(shift(clean(read("course/appendix_reading.md")).replace("# Further reading and resources", "# Appendix B — Further reading and resources", 1)))
    md.append(shift("# Appendix C — Cheat sheet\n" + clean(read("docs/cheatsheet.md")).split("\n", 1)[1]))
    md.append(shift("# Appendix D — Code under test\n\nThe complete `src/autotest` library that every lab tests. "
                    "Read it only after designing tests from the specifications — that is the point of Chapter 6 and Lab 3.\n"))
    for p in sorted((ROOT / "src/autotest").glob("*.py")):
        md.append(shift(f"\n## {p.name}\n") + source(str(p.relative_to(ROOT))))
    md.append(shift("# Appendix E — Course tooling\n\n## Shared fixtures and options\n") + source("conftest.py"))
    md.append(shift("\n## Mutation tester (Lab 12)\n") + source("tools/mini_mutate.py"))
    md.append(shift("\n## Requirements used for traceability (Lab 13)\n") + source("docs/requirements.csv", "text"))
    md.append(shift("# Appendix F — Self-check answers\n\nAnswers to the *Check your understanding* questions at the end of each chapter. "
                    "Try the questions first.\n"))
    md.append("".join(answers))
    if instructor:
        md.append(part_heading("Instructor material"))
        md.append(shift(clean(read("COURSE_DESIGN.md"))))
        md.append(shift(clean(read("docs/instructor_guide.md"))))
        md.append(shift("# Instructor solutions\n\n" + clean(read("solutions/README.md")).split("\n", 1)[1]))
        for p in sorted((ROOT / "solutions").glob("*.py")):
            if p.name != "__init__.py":
                md.append(shift(f"\n## {p.name}\n") + source(str(p.relative_to(ROOT))))
        md.append(shift("\n## bms_nan_fix.patch (Lab 8)\n") + source("solutions/bms_nan_fix.patch", "diff"))
        md.append(shift("\n## Capstone grader\n") + source("capstone/grade.py"))
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
            "--template", str(ROOT / "tools/pdf/template.html"), "--toc", "--toc-depth=2",
            "--highlight-style=pygments", "--metadata", f"pagetitle={TITLE}",
            "-V", f"styles={(ROOT / 'tools/pdf/style.css').read_text(encoding='utf-8')}",
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
