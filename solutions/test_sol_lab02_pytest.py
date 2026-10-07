"""Solutions - Lab 2 (pytest)."""
import pytest

from autotest.bms import max_charge_current
from autotest.sensors import SensorFault, TemperatureSensor


class ScriptedADC:
    def __init__(self, *values):
        self.values = list(values)

    def read(self):
        return self.values.pop(0)


# 1 - parametrization replaces the copy/paste
@pytest.mark.parametrize("counts", [0, 4095], ids=["short-to-ground", "open-circuit"])
def test_rails(counts):
    with pytest.raises(SensorFault):
        TemperatureSensor(ScriptedADC(counts)).read()


# 2 - factory fixture
@pytest.fixture
def sensor_factory():
    def make(*counts, filter_len=4):
        return TemperatureSensor(ScriptedADC(*counts), filter_len=filter_len)
    return make


def test_filter_averages_three_samples(sensor_factory):
    s = sensor_factory(1024, 2048, 3072)
    for _ in range(3):
        last = s.read_filtered()
    assert last == pytest.approx(TemperatureSensor.T_MIN + 190 * 2048 / 4095)


# 3 - parametrize with ids and an expected-failure row
@pytest.mark.parametrize("soc, expected", [
    pytest.param(0, 100.0, id="empty"),
    pytest.param(80, 100.0, id="taper-starts"),
    pytest.param(90, 50.0, id="half-way"),
    pytest.param(100, 0.0, id="full"),
    pytest.param(95, 50.0, id="old-spec-value", marks=pytest.mark.xfail(reason="superseded spec: was 50 A", strict=True)),
])
def test_charge_current_by_soc(soc, expected):
    assert max_charge_current(soc, 25) == pytest.approx(expected)


# 4 - tmp_path + exceptions
def load_calibration(path):
    key, _, value = path.read_text().strip().partition("=")
    if key != "circumference":
        raise ValueError(f"unexpected key {key!r}")
    return float(value)


def test_calibration_file(tmp_path):
    f = tmp_path / "cal.txt"
    f.write_text("circumference=1.95\n")
    assert load_calibration(f) == pytest.approx(1.95)


def test_calibration_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_calibration(tmp_path / "nope.txt")


def test_calibration_malformed(tmp_path):
    f = tmp_path / "cal.txt"
    f.write_text("radius=0.3")
    with pytest.raises(ValueError, match="unexpected key"):
        load_calibration(f)
