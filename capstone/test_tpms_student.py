"""Capstone starter - replace/extend with YOUR test suite for autotest.tpms.

Read capstone/README.md first. Grade yourself with:  python capstone/grade.py
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
