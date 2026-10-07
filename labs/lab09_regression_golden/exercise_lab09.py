"""Lab 9 exercises - regression: triage a bug report, golden transcript, replay.

  Run it:       python course.py exercise 9
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the test.
  Done when:    `python course.py progress` shows every test of Lab 9 passing.

Note on golden files: the FIRST run of a golden test creates the file and fails on purpose (nothing to compare
with yet). Read the new file carefully - it is now your specification - then run again.
"""
from autotest.can import CANFrame, e2e_protect
from autotest.diagnostics import DiagnosticManager
from autotest.ecu import WHEEL_SPEED_MSG, InstrumentCluster
from autotest.learn import todo


def test_bug_120_invalid_flag_shows_dashes(bus, clock):
    """Exercise 1 - you receive BUG-120: 'the cluster shows 0 instead of -- when the sender says valid=0'.
    Rule #1 of regression work: REPRODUCE IT WITH A TEST FIRST. (Be ready for a surprise.)

    Hint 1: payload = WHEEL_SPEED_MSG.encode({"speed_kmh": 0.0, "valid": 0});  data = e2e_protect(payload, 0)
    Hint 2: send it:  bus.send(CANFrame(0x1A0, data));  then check cluster.displayed_speed()
    Hint 3: if your test PASSES, the bug is not reproducible: say so in a comment - the test stays as a guard,
            and the ticket is closed 'cannot reproduce' with this test as the evidence.
    """
    todo("reproduce BUG-120")


def test_uds_session_transcript(golden):
    """Exercise 2 - record a diagnostic session as a golden file `golden/uds_session.txt`:
    read DTCs, read VIN, clear DTCs, read DTCs again, an unknown service (hex bytes for each request and response).

    Hint 1: d = DiagnosticManager(fail_threshold=1);  d.report("U0121", failed=True)   # one stored code
    Hint 2: requests: b"\\x19\\x02\\xFF"   b"\\x22\\xF1\\x90"   b"\\x14\\xFF\\xFF\\xFF"   b"\\x19\\x02\\xFF"   b"\\x3E\\x00"
    Hint 3: build text lines like   f"{label:<16} {req.hex(' ')}  ->  {d.handle_request(req).hex(' ')}"   and call   golden("uds_session.txt", text)
    Then READ the generated file: do the response bytes match the UDS rules from Chapter 3 (positive = SID + 0x40, negative = 7F ...)?
    """
    todo("record the session as a golden file")


# Exercise 3 (no code) - edit labs/lab09_regression_golden/data/drive_cycle.log by hand: change one speed value, run
# `python course.py lab 9`, and read the diff pytest prints. Then undo the change with `git checkout` on that file.
# Write one sentence: what is the danger of blindly running  pytest --update-golden ?
