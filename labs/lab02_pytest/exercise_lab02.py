"""Lab 2 exercises. Run: pytest labs/lab02_pytest/exercise_lab02.py -v"""
import pytest

from autotest.sensors import TemperatureSensor, SensorFault, wheel_speed_kmh
from autotest.bms import max_charge_current


class ScriptedADC:
    def __init__(self, *values):
        self.values = list(values)

    def read(self):
        return self.values.pop(0)


# Exercise 1 - parametrize: convert this copy-pasted test into ONE parametrized test
def test_rails_a():
    with pytest.raises(SensorFault):
        TemperatureSensor(ScriptedADC(0)).read()


def test_rails_b():
    with pytest.raises(SensorFault):
        TemperatureSensor(ScriptedADC(4095)).read()


# Exercise 2 - fixture: build a `sensor_factory` fixture that returns a function
# making a TemperatureSensor from a list of ADC counts, then test read_filtered():
# the average of readings 1024, 2048, 3072 after three calls must be the mid-scale temperature.
def test_filter_averages_three_samples():
    pytest.fail("TODO")


# Exercise 3 - parametrize with ids and pytest.param(..., marks=pytest.mark.xfail):
# cover max_charge_current at soc in (0, 80, 90, 100) for a 25 degC battery.
def test_charge_current_by_soc():
    pytest.fail("TODO")


# Exercise 4 - use tmp_path + monkeypatch: write a function `load_calibration(path)` in
# THIS file that reads "circumference=1.95" from a file, then test it for a good file,
# a missing file (FileNotFoundError) and a malformed line (ValueError).
def test_calibration_file():
    pytest.fail("TODO")
