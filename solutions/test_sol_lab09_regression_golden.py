"""Solutions - Lab 9 (regression / golden)."""
import pytest

from autotest.bus import VirtualCANBus
from autotest.can import CANFrame, e2e_protect
from autotest.diagnostics import DiagnosticManager
from autotest.ecu import WHEEL_SPEED_MSG, InstrumentCluster

pytestmark = pytest.mark.regression


def test_bug_120_invalid_flag_shows_dashes(bus, clock):
    """BUG-120 'shows 0 instead of -- when valid=0': NOT reproducible - the cluster already maps
    valid=0 to '--'. The test stays as a regression guard and the ticket is closed 'cannot reproduce'
    (with this test as the evidence)."""
    cluster = InstrumentCluster(bus, clock)
    payload = WHEEL_SPEED_MSG.encode({"speed_kmh": 0.0, "valid": 0})
    bus.send(CANFrame(0x1A0, e2e_protect(payload, 0)))
    assert cluster.displayed_speed() == "--"


def test_uds_session_transcript(golden):
    d = DiagnosticManager(fail_threshold=1)
    d.report("U0121", failed=True)
    lines = []
    for label, req in [("read DTCs", b"\x19\x02\xFF"), ("read VIN", b"\x22\xF1\x90"),
                       ("clear DTCs", b"\x14\xFF\xFF\xFF"), ("read DTCs again", b"\x19\x02\xFF"),
                       ("unknown service", b"\x3E\x00")]:
        lines.append(f"{label:<16} {req.hex(' ')}  ->  {d.handle_request(req).hex(' ')}")
    golden("uds_session.txt", "\n".join(lines) + "\n")
