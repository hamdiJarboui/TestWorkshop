"""Capstone starter - replace/extend with YOUR test suite for autotest.tpms.

  1. Read capstone/README.md (the specification S1..S9) and Chapter 17 (the recipe).
  2. Write tests here (split into more files if you like). They must PASS on the correct code.
  3. Grade yourself:   python course.py capstone     (injects 17 hidden defects, one at a time)
     The grader tells you the SYMPTOM of every defect you missed - use it to find the test you forgot.
"""
import pytest

from autotest.tpms import LeakDetector, TyreStatus, classify, normalise_pressure, validate_sensor_id


@pytest.mark.smoke
def test_nominal_tyre_is_ok():
    assert classify(230, 20) is TyreStatus.OK


# TODO 1  normalisation (S1)               -> exact values, cold and hot
# TODO 2  classification (S3-S6)           -> every threshold: just below / on / just above
# TODO 3  nominal override                 -> classify(..., nominal=250)
# TODO 4  input validation (S8, S9)        -> every limit: on it (ok) and just beyond (ValueError)
# TODO 5  leak detection (S7)              -> drop sizes, window edges, recovery, falling slowly
# TODO 6  one property-based test         -> classify is monotonic in pressure
# TODO 7  mark requirement tests          -> @pytest.mark.requirement("REQ-TPMS-001") / "REQ-TPMS-002"
