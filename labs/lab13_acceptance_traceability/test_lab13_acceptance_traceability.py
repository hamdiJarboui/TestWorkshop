"""Lab 13 - acceptance testing, requirement traceability and hardware-in-the-loop (HIL) switching.

ISO 26262 / ASPICE style evidence: every requirement is linked to >= 1 verifying test and
the report shows PASS/FAIL per requirement:

    pytest labs --req-report -q
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

import pytest

from autotest.bms import BatteryManagementSystem, BMSFault
from autotest.can import CANFrame
from autotest.diagnostics import DiagnosticManager
from autotest.sensors import SensorFault, TemperatureSensor

ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = {row["id"]: row for row in csv.DictReader((ROOT / "docs" / "requirements.csv").open())}


# =============================================================================================
# A. Acceptance scenarios (Given / When / Then) - written in the customer's language
# =============================================================================================
@pytest.mark.requirement("REQ-CAN-001")
class TestFeatureFrameValidation:
    """Feature: the gateway refuses malformed identifiers."""

    @pytest.mark.parametrize("ident, extended, ok", [
        (0x000, False, True), (0x7FF, False, True), (0x800, False, False),
        (0x800, True, True), (0x1FFFFFFF, True, True), (0x20000000, True, False), (-1, False, False),
    ])
    def test_scenario_identifier_ranges(self, ident, extended, ok):
        # Given a gateway that builds frames
        # When it is asked for identifier <ident> (standard or extended)
        # Then the frame exists only if the identifier fits the identifier field
        if ok:
            assert CANFrame(ident, is_extended=extended).arbitration_id == ident
        else:
            with pytest.raises(ValueError):
                CANFrame(ident, is_extended=extended)


@pytest.mark.requirement("REQ-BMS-003")
class TestFeatureOvervoltageProtection:
    def test_scenario_one_weak_cell_in_a_healthy_pack(self):
        # Given a 96-cell pack where every cell is at 3.9 V
        cells = [3.9] * 96
        bms = BatteryManagementSystem()
        assert bms.evaluate(cells, 25) is BMSFault.NONE
        # When ONE cell rises to 4.21 V
        cells[57] = 4.21
        # Then an overvoltage fault is raised
        assert bms.evaluate(cells, 25) is BMSFault.OVERVOLTAGE

    def test_scenario_cell_exactly_at_the_limit_is_still_allowed(self):
        assert BatteryManagementSystem().evaluate([4.20] * 4, 25) is BMSFault.NONE


@pytest.mark.requirement("REQ-DIAG-001")
class TestFeatureDtcDebouncing:
    @pytest.mark.parametrize("n", [1, 2, 3, 5])
    def test_scenario_code_is_confirmed_only_after_n_consecutive_failures(self, n):
        # Given a manager that confirms after n failures
        diag = DiagnosticManager(fail_threshold=n)
        # When the monitor fails n-1 times
        for _ in range(n - 1):
            diag.report("P0301", failed=True)
        # Then nothing is stored; one more failure confirms it
        assert diag.stored_codes() == []
        diag.report("P0301", failed=True)
        assert diag.stored_codes() == ["P0301"]

    def test_scenario_a_good_cycle_resets_the_failure_streak(self):
        diag = DiagnosticManager(fail_threshold=3)
        for outcome in (True, True, False, True, True):
            diag.report("P0301", failed=outcome)
        assert diag.stored_codes() == []        # failures were never CONSECUTIVE enough


# =============================================================================================
# B. Traceability checks - the test suite tests its own documentation
# =============================================================================================
def _markers_in_repo():
    found = {}
    pattern = re.compile(r'mark\.requirement\("(REQ-[A-Z]+-\d{3})"\)')
    for folder in ("labs", "solutions"):
        for path in (ROOT / folder).rglob("*.py"):
            if path.name.startswith("exercise_"):
                continue
            for req in pattern.findall(path.read_text()):
                found.setdefault(req, set()).add(path.name)
    return found


def test_every_requirement_is_verified_by_at_least_one_test():
    verified = _markers_in_repo()
    missing = sorted(set(REQUIREMENTS) - set(verified))
    assert not missing, f"requirements without a verifying test: {missing}"


def test_no_test_refers_to_an_unknown_requirement():
    unknown = sorted(set(_markers_in_repo()) - set(REQUIREMENTS))
    assert not unknown, f"typo or deleted requirement? {unknown}"


def test_requirement_report_option_prints_a_matrix():
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "labs/lab05_integration", "-q", "--req-report", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout
    assert "REQ-CLU-001" in r.stdout and "PASS" in r.stdout
    assert "REQ-CAN-003" in r.stdout


# =============================================================================================
# C. SIL / HIL: one test body, two back-ends
# =============================================================================================
class SimulatedADC:
    """SIL back-end: always available."""

    def __init__(self, counts=2048):
        self.counts = counts

    def read(self):
        return self.counts


class BenchADC:
    """HIL back-end: talks to a real bench (serial / CAN-FD / NI-DAQ ...). Not available here."""

    def __init__(self):
        raise RuntimeError("no hardware bench connected")  # replaced by a real driver in the lab

    def read(self):  # pragma: no cover
        raise NotImplementedError


@pytest.fixture(params=["sil", pytest.param("hil", marks=pytest.mark.hil)])
def adc(request):
    return SimulatedADC() if request.param == "sil" else BenchADC()


def test_mid_scale_temperature_is_plausible_on_every_back_end(adc):
    # Same assertions on the simulator (default) and on the bench (pytest --hil)
    assert -40 < TemperatureSensor(adc).read() < 150


def test_hil_tests_are_skipped_without_the_flag(pytestconfig):
    if pytestconfig.getoption("--hil"):
        pytest.skip("running with --hil: this check only applies to the default run")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-q", "-rs", "-p", "no:cacheprovider", "-k", "mid_scale"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert "needs hardware" in r.stdout
