"""Solutions - Lab 3 (test-design techniques)."""
import pytest

from autotest.bms import BatteryManagementSystem, BMSFault

bms = BatteryManagementSystem()
OK = [3.7, 3.7]


# 1 - boundaries: ON the limit (still healthy) and just beyond it (fault)
@pytest.mark.parametrize("cells, temp, expected", [
    ([4.20, 3.7], 25, BMSFault.NONE), ([4.21, 3.7], 25, BMSFault.OVERVOLTAGE),
    ([3.00, 3.7], 25, BMSFault.NONE), ([2.99, 3.7], 25, BMSFault.UNDERVOLTAGE),
    (OK, 60.0, BMSFault.NONE), (OK, 60.1, BMSFault.OVERTEMPERATURE),
    (OK, -20.0, BMSFault.NONE), (OK, -20.1, BMSFault.UNDERTEMPERATURE),
])
def test_boundaries(cells, temp, expected):
    assert bms.evaluate(cells, temp) is expected


# 2 - decision table for simultaneous faults. Rule: voltage faults outrank temperature faults,
#     over-voltage outranks under-voltage.
#
#   over-V | under-V | over-T | result
#   -------+---------+--------+-------------
#    yes   |   yes   |   no   | OVERVOLTAGE
#    yes   |   no    |  yes   | OVERVOLTAGE
#    no    |   yes   |  yes   | UNDERVOLTAGE
#    no    |   no    |  yes   | OVERTEMPERATURE
@pytest.mark.parametrize("cells, temp, expected", [
    ([4.3, 2.9], 25, BMSFault.OVERVOLTAGE),
    ([4.3, 3.7], 70, BMSFault.OVERVOLTAGE),
    ([2.9, 3.7], 70, BMSFault.UNDERVOLTAGE),
    ([3.7, 3.7], 70, BMSFault.OVERTEMPERATURE),
])
def test_priority_between_faults(cells, temp, expected):
    assert bms.evaluate(cells, temp) is expected


# 3 - the spec is silent about an empty cell list. We chose "reject loudly" because a BMS that
#     silently reports 'healthy' with NO data is the dangerous option. Question logged for the
#     product owner: should this be a distinct communication-fault state instead of an exception?
def test_empty_cell_list():
    with pytest.raises(ValueError):
        bms.evaluate([], 25)
