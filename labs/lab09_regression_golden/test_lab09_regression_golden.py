"""Lab 9 - regression testing: bug-guard tests, golden files and log replay.

Rule: every defect that ever escaped gets a test BEFORE it is fixed. Golden files
protect complex outputs (reports, logs) that are tedious to assert field-by-field.

Create/refresh golden files deliberately with:  pytest labs/lab09_regression_golden --update-golden
(then READ the git diff - an updated golden file is a reviewed change, not a formality)
"""
from pathlib import Path

import pytest

from autotest.bus import VirtualCANBus
from autotest.can import CANFrame
from autotest.clock import FakeClock
from autotest.diagnostics import DiagnosticManager
from autotest.ecu import InstrumentCluster, WheelSpeedECU

pytestmark = pytest.mark.regression
DATA = Path(__file__).parent / "data"


# ---- 1. bug-guard tests: name them after the ticket ------------------------------------------
def test_bug_087_alive_counter_wrap_15_to_0_was_rejected(clock):
    """BUG-087: after 16 frames the 4-bit counter wrapped and the cluster went blank."""
    bus = VirtualCANBus()
    ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)
    for i in range(40):                       # > 2 full counter cycles
        ecu.send_speed(i)
        assert cluster.displayed_speed() == str(i), f"frame {i}"


def test_bug_093_crc_error_must_not_update_last_rx_time(clock):
    """BUG-093: garbage frames kept the timeout from expiring (cluster showed stale speed)."""
    bus = VirtualCANBus()
    cluster = InstrumentCluster(bus, clock)
    WheelSpeedECU(bus).send_speed(80)
    for _ in range(5):
        clock.advance(0.05)
        bus.send(CANFrame(0x1A0, b"\x00\x01\x02\x03\x04"))   # invalid CRC
    assert cluster.displayed_speed() == "--"


# ---- 2. golden file for a text report ------------------------------------------------------------
def test_dtc_report_matches_golden(golden):
    d = DiagnosticManager(fail_threshold=2, heal_threshold=2)
    for _ in range(2):
        d.report("U0121", failed=True)         # confirmed
    d.report("P0300", failed=True)             # pending only
    for _ in range(2):
        d.report("U0100", failed=True)
    for _ in range(2):
        d.report("U0100", failed=False)        # confirmed then healed
    golden("dtc_report.txt", d.export_report())


# ---- 3. replaying a recorded drive cycle ---------------------------------------------------------------
def replay(path: Path):
    """Feed a recorded log into a fresh cluster; return what the driver would have seen."""
    clock, bus = FakeClock(), VirtualCANBus()
    cluster = InstrumentCluster(bus, clock)
    seen = []
    for line in path.read_text(encoding="utf-8").splitlines():
        t, can_id, data = line.split()
        clock.advance(float(t) - clock.now())
        bus.send(CANFrame(int(can_id, 16), bytes.fromhex(data)))
        seen.append(f"{float(t):6.3f}s  {cluster.displayed_speed():>3}")
    return "\n".join(seen) + "\n", cluster


def test_recorded_drive_cycle_shows_the_same_dashboard_as_last_release(golden):
    transcript, _ = replay(DATA / "drive_cycle.log")
    golden("drive_cycle_display.txt", transcript)


def test_replay_of_the_recording_raises_no_dtc():
    _, cluster = replay(DATA / "drive_cycle.log")
    assert cluster.diag.stored_codes() == []   # one recorded bit error is only debounced


def test_bug_130_single_bit_error_must_cost_exactly_one_frame(clock):
    """BUG-130 (found by the replay in this lab): a CRC error left the expected alive counter
    unchanged, so the NEXT good frame failed the counter check too -> two losses, and with
    fail_threshold=2 a DTC for what was a single bit error."""
    bus = VirtualCANBus()
    ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)
    ecu.send_speed(10)
    flip = lambda f: CANFrame(f.arbitration_id, bytes([f.data[0] ^ 1]) + f.data[1:])
    bus.add_fault(flip)
    ecu.send_speed(20)                       # corrupted in flight
    bus.clear_faults()
    ecu.send_speed(30)                       # must be accepted immediately
    assert cluster.displayed_speed() == "30"
    assert cluster.diag.stored_codes() == []
