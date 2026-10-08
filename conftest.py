"""Shared fixtures and a tiny requirement-traceability plugin for the whole course."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest

from autotest.bus import VirtualCANBus
from autotest.clock import FakeClock


def pytest_addoption(parser):
    g = parser.getgroup("autotest course")
    g.addoption("--hil", action="store_true", help="run tests marked 'hil' (needs hardware)")
    g.addoption("--update-golden", action="store_true", help="rewrite golden files (Lab 9)")
    g.addoption("--req-report", action="store_true", help="print requirement traceability matrix (Lab 13)")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--hil"):
        skip_hil = pytest.mark.skip(reason="needs hardware: run with --hil")
        for item in items:
            if "hil" in item.keywords:
                item.add_marker(skip_hil)


# ---- shared fixtures ---------------------------------------------------------
@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def bus() -> VirtualCANBus:
    return VirtualCANBus()


@pytest.fixture
def golden(request):
    """Compare text with a stored golden file; `--update-golden` rewrites it."""
    update = request.config.getoption("--update-golden")
    base = Path(request.node.fspath).parent / "golden"

    def check(name: str, actual: str) -> None:
        path = base / name
        if update or not path.exists():
            base.mkdir(exist_ok=True)
            path.write_text(actual, encoding="utf-8")
            if not update:
                pytest.fail(f"golden file {path} did not exist - created it; re-run to verify")
            return
        assert actual == path.read_text(encoding="utf-8"), f"output differs from {path.name}; inspect, then --update-golden"

    return check


# ---- requirement traceability ------------------------------------------------
_trace: dict[str, list[tuple[str, str]]] = defaultdict(list)


def pytest_runtest_logreport(report):
    if report.when == "call":
        for req in getattr(report, "_reqs", []):
            _trace[req].append((report.nodeid, report.outcome))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    rep._reqs = [m.args[0] for m in item.iter_markers("requirement") if m.args]


def pytest_terminal_summary(terminalreporter, config):
    if not config.getoption("--req-report"):
        return
    tr = terminalreporter
    tr.section("requirement traceability")
    for req in sorted(_trace):
        results = _trace[req]
        verdict = "PASS" if all(o == "passed" for _, o in results) else "FAIL"
        tr.write_line(f"{req:<14} {verdict}  ({len(results)} tests)")
        for nodeid, outcome in results:
            tr.write_line(f"    {outcome:<7} {nodeid}")
