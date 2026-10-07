"""Lab 3 - test-design techniques (black box) on the BMS charge-current rule.

Spec under test: autotest.bms.max_charge_current (read its docstring FIRST - that is
the 'specification'; we design tests from it without looking at the implementation).
"""
import pytest

from autotest.bms import max_charge_current

RATED = 100.0


# ---- Equivalence partitioning: one representative per class ----------------------
# Temperature classes:  <0 | 0..<10 | 10..45 | >45          (SOC fixed at a neutral 50 %)
@pytest.mark.requirement("REQ-BMS-001")
@pytest.mark.parametrize(
    "temp, expected",
    [(-20, 0.0), (5, 25.0), (25, 100.0), (60, 0.0)],
    ids=["too-cold", "cold", "normal", "too-hot"],
)
def test_temperature_partitions(temp, expected):
    assert max_charge_current(soc=50, temp_c=temp) == pytest.approx(expected)


# ---- Boundary value analysis: values ON and either side of every boundary --------
@pytest.mark.requirement("REQ-BMS-001")
@pytest.mark.parametrize(
    "temp, expected",
    [
        (-0.1, 0.0), (0.0, 25.0), (0.1, 25.0),        # 0 degC boundary
        (9.9, 25.0), (10.0, 100.0), (10.1, 100.0),    # 10 degC boundary
        (44.9, 100.0), (45.0, 100.0), (45.1, 0.0),    # 45 degC boundary
    ],
)
def test_temperature_boundaries(temp, expected):
    assert max_charge_current(soc=50, temp_c=temp) == pytest.approx(expected)


@pytest.mark.requirement("REQ-BMS-002")
@pytest.mark.parametrize(
    "soc, expected",
    [(0, 100.0), (79.9, 100.0), (80.0, 100.0), (80.1, 99.5), (90, 50.0), (99, 5.0), (100, 0.0)],
)
def test_soc_taper_boundaries(soc, expected):
    assert max_charge_current(soc=soc, temp_c=25) == pytest.approx(expected)


@pytest.mark.parametrize("soc", [-0.1, 100.1])
def test_invalid_soc_is_rejected(soc):
    with pytest.raises(ValueError):
        max_charge_current(soc=soc, temp_c=25)


# ---- Decision table: every combination of conditions -> expected action ----------
#   cold   | hot   | soc>80 | soc>=100 | result
#   -------+-------+--------+----------+----------------------------------
#   no     | no    | no     | no       | full current
#   cold   |       |        |          | 25 % current
#   no     | no    | yes    | no       | tapered
#   cold   | no    | yes    | no       | 25 % AND tapered (rules combine!)
#   any    | hot   | any    | any      | 0
DECISION_TABLE = [
    # soc, temp, expected
    (50, 25, 100.0),    # normal
    (50, 5, 25.0),      # cold only
    (90, 25, 50.0),     # taper only
    (90, 5, 12.5),      # cold + taper (interaction - the classic missed case)
    (50, 50, 0.0),      # hot
    (90, 50, 0.0),      # hot beats taper
    (100, 25, 0.0),     # full
]


@pytest.mark.parametrize("soc, temp, expected", DECISION_TABLE)
def test_decision_table(soc, temp, expected):
    assert max_charge_current(soc, temp) == pytest.approx(expected)


# ---- Invariants / oracle-free checks ---------------------------------------------
def test_current_never_negative_or_above_rated_over_whole_grid():
    for soc in range(0, 101, 5):
        for temp in range(-30, 71, 5):
            i = max_charge_current(soc, temp)
            assert 0.0 <= i <= RATED, (soc, temp, i)


def test_current_is_monotonic_non_increasing_in_soc():
    values = [max_charge_current(s / 2, 25) for s in range(0, 201)]
    assert values == sorted(values, reverse=True)
