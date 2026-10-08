#!/usr/bin/env python3
"""mini_mutate - a ~120 line mutation tester, small enough to read in class.

Idea: coverage tells you which lines RAN; mutation testing tells you whether your
assertions would NOTICE if the line were wrong. We make one small change (a "mutant")
to the code under test, run the tests, and expect them to FAIL ("kill" the mutant).
A mutant that survives points at a missing or weak assertion (or is an "equivalent mutant":
changed code, identical behaviour, which no test can kill).

Exit status: 0 normally (survivors are information, not an error), 1 with --strict if any survive,
2 if the unmutated code already fails the tests.

Example
    python tools/mini_mutate.py --target src/autotest/bms.py --function max_charge_current \
        --tests labs/lab03_black_box/test_lab03_black_box.py
"""
from __future__ import annotations

import argparse
import ast
import copy
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SWAPS = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult,
    ast.And: ast.Or, ast.Or: ast.And,
}


class Mutator(ast.NodeTransformer):
    """Visits every mutable site in order; mutates only the one whose index == target."""

    def __init__(self, target: int, function: str | None):
        self.target, self.function = target, function
        self.count, self.sites, self._inside = 0, [], function is None

    def visit_FunctionDef(self, node):
        was = self._inside
        if self.function and node.name == self.function:
            self._inside = True
        self.generic_visit(node)
        self._inside = was
        return node

    def _site(self, node, description):
        index, self.count = self.count, self.count + 1
        self.sites.append((node.lineno, description))
        return index == self.target

    def visit_Compare(self, node):
        self.generic_visit(node)
        if self._inside:
            for i, op in enumerate(node.ops):
                if type(op) in SWAPS and self._site(node, f"{type(op).__name__} -> {SWAPS[type(op)].__name__}"):
                    node.ops[i] = SWAPS[type(op)]()
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if self._inside and type(node.op) in SWAPS and self._site(node, f"{type(node.op).__name__} -> {SWAPS[type(node.op)].__name__}"):
            node.op = SWAPS[type(node.op)]()
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if self._inside and self._site(node, f"{type(node.op).__name__} -> {SWAPS[type(node.op)].__name__}"):
            node.op = SWAPS[type(node.op)]()
        return node

    def visit_Constant(self, node):
        if self._inside and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            if self._site(node, f"constant {node.value!r} -> {node.value + 1!r}"):
                return ast.copy_location(ast.Constant(node.value + 1), node)
        return node


def run_tests(workdir: Path, tests: list[str], timeout: int) -> bool:
    """True when the test run PASSED."""
    # Without this, two same-sized mutants written within one second would reuse the previous
    # mutant's stale .pyc (bytecode is validated by source mtime in whole seconds + size).
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *tests],
                           cwd=workdir, capture_output=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return False  # an infinite loop counts as detected
    return r.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", required=True, help="python file to mutate (relative to repo root)")
    ap.add_argument("--function", help="only mutate inside this function")
    ap.add_argument("--tests", nargs="+", required=True, help="test files / dirs to run")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--list", action="store_true", help="only list mutation sites")
    ap.add_argument("--strict", action="store_true",
                    help="exit with status 1 if any mutant survives (for CI gates; survivors can be equivalent mutants)")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    target = root / args.target
    tree = ast.parse(target.read_text(encoding="utf-8"))
    probe = Mutator(-1, args.function)
    probe.visit(copy.deepcopy(tree))
    print(f"{len(probe.sites)} mutants in {args.target}" + (f"::{args.function}" if args.function else ""))
    if args.list:
        for i, (line, desc) in enumerate(probe.sites):
            print(f"  #{i:02d} line {line}: {desc}")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "proj"
        shutil.copytree(root, work, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".pytest_cache", ".hypothesis", "htmlcov", ".coverage"))
        mutated_file = work / args.target
        if not run_tests(work, args.tests, args.timeout):
            print("The unmutated code already FAILS the tests - fix that first.")
            return 2
        survivors = []
        for i, (line, desc) in enumerate(probe.sites):
            m = Mutator(i, args.function)
            mutated_file.write_text(ast.unparse(m.visit(copy.deepcopy(tree))), encoding="utf-8")
            killed = not run_tests(work, args.tests, args.timeout)
            print(f"  #{i:02d} line {line:>3} {desc:<28} {'killed' if killed else 'SURVIVED'}")
            if not killed:
                survivors.append((i, line, desc))
        total = len(probe.sites)
        score = 100 * (total - len(survivors)) / total if total else 100.0
        print(f"\nmutation score: {total - len(survivors)}/{total} = {score:.0f} %")
        for i, line, desc in survivors:
            print(f"  survivor #{i:02d} (line {line}): {desc}  -> which assertion should have failed?")
        return 1 if (survivors and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
