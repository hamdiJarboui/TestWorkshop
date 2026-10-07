"""Reference capstone suite: must catch 17/17 defects (CI runs `capstone/grade.py --min-score 100`)."""
import pytest
from hypothesis import given, strategies as st

from autotest.tpms import LeakDetector, TyreStatus, classify, normalise_pressure, validate_sensor_id

S = TyreStatus


# ---- S1 normalisation -----------------------------------------------------------------------------
@pytest.mark.parametrize("kpa, temp, expected", [
    (230, 20, 230.0), (230, -40, 230 * 293.15 / 233.15), (230, 125, 230 * 293.15 / 398.15), (0, 20, 0.0),
])
def test_normalisation_follows_gay_lussac_exactly(kpa, temp, expected):
    assert normalise_pressure(kpa, temp) == pytest.approx(expected, rel=1e-12)


def test_cold_tyre_reads_lower_than_the_same_pressure_when_hot():
    assert normalise_pressure(200, 60) < 200 < normalise_pressure(200, -10)
    # a hot tyre at 200 kPa is really *under*-inflated once normalised to 20 degC


# ---- S3-S6 classification ----------------------------------------------------------------------------
@pytest.mark.requirement("REQ-TPMS-001")
@pytest.mark.parametrize("kpa, expected", [
    (0, S.CRITICAL), (137.99, S.CRITICAL), (138.0, S.LOW), (138.01, S.LOW),
    (183.99, S.LOW), (184.0, S.OK), (184.01, S.OK),
    (230, S.OK), (298.99, S.OK), (299.0, S.OK), (299.01, S.HIGH), (700, S.HIGH),
])
def test_thresholds_at_20_degc(kpa, expected):
    assert classify(kpa, 20) is expected


def test_temperature_changes_the_verdict_for_the_same_gauge_reading():
    # 200 kPa on a gauge: fine at 20 degC, but 20 degC-equivalent is only 160 kPa when it is 80 degC
    assert classify(200, 20) is S.OK
    assert classify(200, 80) is S.LOW


def test_custom_nominal_pressure():
    assert classify(230, 20, nominal=300) is S.LOW        # 76.7 % of 300
    assert classify(230, 20, nominal=250) is S.OK


def test_default_nominal_is_230():
    assert classify(183.9, 20) is S.LOW and classify(184.0, 20) is S.OK


# ---- S8 sensor ids ----------------------------------------------------------------------------------------
@pytest.mark.parametrize("good", ["0A1B2C3D", "ffffffff", "00000000", "AbCdEf01"])
def test_valid_ids_are_normalised_to_upper_case(good):
    assert validate_sensor_id(good) == good.upper()


@pytest.mark.parametrize("bad", ["", "0A1B2C3", "0A1B2C3D4", "0A1B2C3G", " 0A1B2C3", "0A1B2C3D\n", "0x1B2C3D"])
def test_invalid_ids_are_rejected(bad):
    with pytest.raises(ValueError):
        validate_sensor_id(bad)


# ---- S9 range checks ---------------------------------------------------------------------------------------
@pytest.mark.parametrize("kpa, temp", [(0, 20), (700, 20), (230, -40), (230, 125), (0, -40), (700, 125)])
def test_limits_themselves_are_accepted(kpa, temp):
    classify(kpa, temp)


@pytest.mark.parametrize("kpa, temp", [(-0.01, 20), (700.01, 20), (230, -40.01), (230, 125.01)])
def test_just_beyond_the_limits_is_rejected(kpa, temp):
    with pytest.raises(ValueError):
        classify(kpa, temp)


# ---- S7 leak detection ---------------------------------------------------------------------------------------
@pytest.fixture
def leak():
    return LeakDetector()


@pytest.mark.requirement("REQ-TPMS-002")
def test_drop_of_exactly_20_kpa_raises_the_alarm(leak):
    leak.add(0, 230)
    assert leak.add(10, 210) is True


@pytest.mark.requirement("REQ-TPMS-002")
def test_drop_of_19_99_kpa_does_not(leak):
    leak.add(0, 230)
    assert leak.add(10, 210.01) is False


def test_slow_leak_across_the_window_is_not_a_rapid_loss(leak):
    for i, t in enumerate(range(0, 300, 30)):
        assert leak.add(t, 230 - i * 2) is False         # 2 kPa per 30 s


def test_sample_exactly_on_the_window_edge_still_counts(leak):
    leak.add(0, 230)
    assert leak.add(60, 210) is True


def test_sample_just_outside_the_window_is_forgotten(leak):
    leak.add(0, 230)
    assert leak.add(60.01, 210) is False


def test_old_samples_expire_even_when_many_arrive(leak):
    leak.add(0, 300)
    for t in range(61, 200, 10):
        leak.add(t, 230)
    assert leak.add(200, 225) is False


def test_window_is_60_seconds_not_30(leak):
    leak.add(0, 250)
    assert leak.add(45, 229) is True


def test_alarm_uses_the_highest_pressure_in_the_window_not_the_lowest(leak):
    leak.add(0, 200)
    leak.add(10, 230)
    assert leak.add(20, 205) is True                      # 25 kPa below the 230 peak
    assert LeakDetector().add(0, 200) is False


def test_rising_pressure_never_alarms(leak):
    assert not any(leak.add(t, 200 + t) for t in range(0, 100, 5))


# ---- property ---------------------------------------------------------------------------------------------------
@given(st.floats(0, 700), st.floats(0, 700), st.floats(-40, 125))
def test_more_pressure_is_never_a_worse_status(a, b, temp):
    order = [S.CRITICAL, S.LOW, S.OK, S.HIGH]
    lo, hi = sorted((a, b))
    assert order.index(classify(lo, temp)) <= order.index(classify(hi, temp))
