"""Lab 2 exercises - pytest: parametrize, fixtures, tmp_path.

  Run it:       python course.py exercise 2
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the
                test; the test then passes only if what you wrote is correct.
  Done when:    `python course.py progress` shows every test of Lab 2 passing.
"""
import pytest

from autotest.bms import max_charge_current
from autotest.learn import todo
from autotest.sensors import SensorFault, TemperatureSensor


class ScriptedADC:
    """A fake ADC that returns the values you give it, one per read()."""

    def __init__(self, *values):
        self.values = list(values)

    def read(self):
        return self.values.pop(0)


# ---------------------------------------------------------------------------------------------
# Exercise 1 - parametrize.  Two copy-pasted tests would look like this:
#
#     def test_rails_a():  with pytest.raises(SensorFault): TemperatureSensor(ScriptedADC(0)).read()
#     def test_rails_b():  with pytest.raises(SensorFault): TemperatureSensor(ScriptedADC(4095)).read()
#
# Write ONE parametrized test instead.
# ---------------------------------------------------------------------------------------------
def test_adc_rail_values_are_sensor_faults():
    """Hint 1: @pytest.mark.parametrize("counts", [0, 4095], ids=["short-to-ground", "open-circuit"])
    Hint 2: the decorated test takes `counts` as an argument and uses it in ScriptedADC(counts).
    Hint 3: remember to turn this into a function with a parameter:  def test_...(counts):
    """
    todo("parametrize over the two rail values")


# ---------------------------------------------------------------------------------------------
# Exercise 2 - a factory fixture: a fixture that returns a FUNCTION so each test chooses its data.
# ---------------------------------------------------------------------------------------------
@pytest.fixture
def sensor_factory():
    """Return a function  make(*counts, filter_len=4)  that builds a TemperatureSensor
    reading the given ADC counts (use ScriptedADC)."""
    todo("write the fixture body: define make(...) and return it")


def test_filter_averages_three_samples(sensor_factory):
    """Counts 1024, 2048, 3072 -> after three read_filtered() calls the result is the average of the three
    temperatures, which equals the temperature of the MIDDLE count (the mapping is linear).

    Hint 1: sensor = sensor_factory(1024, 2048, 3072);  call sensor.read_filtered() three times, keep the last value.
    Hint 2: expected = TemperatureSensor.T_MIN + (TemperatureSensor.T_MAX - TemperatureSensor.T_MIN) * 2048 / 4095
    Hint 3: assert last == pytest.approx(expected)
    """
    todo("use the factory and check the moving average")


# ---------------------------------------------------------------------------------------------
# Exercise 3 - parametrize with ids.  Charge current by SOC at 25 degC (rated current 100 A).
# Spec: no taper up to 80 %, linear taper to 0 A at 100 %.
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("soc, expected", [
    pytest.param(0, 100.0, id="empty"),
    # TODO: add rows for 80, 90 and 100 (work the expected values out from the spec, with an id each)
])
def test_charge_current_by_soc(soc, expected):
    """Hint: max_charge_current(soc, 25) == pytest.approx(expected).
    Hint 2: at 90 % the taper is (100 - 90) / 20 = 0.5 of the full current.
    """
    todo("complete the table (4 rows) and the assertion")


# ---------------------------------------------------------------------------------------------
# Exercise 4 - tmp_path and error cases.  A calibration file contains one line:  circumference=1.95
# ---------------------------------------------------------------------------------------------
def load_calibration(path):
    """Return the wheel circumference (float) from a file containing 'circumference=1.95'.

    Raises FileNotFoundError if the file does not exist, ValueError if the key is not 'circumference'.
    Hint: text = path.read_text()  (a missing file raises FileNotFoundError by itself);  key, _, value = text.strip().partition("=")
    """
    todo("implement load_calibration")


def test_calibration_file_is_read(tmp_path):
    """Hint: create a file in the private tmp_path directory:  f = tmp_path / "cal.txt";  f.write_text("circumference=1.95\\n")"""
    todo("write a good file, call load_calibration, expect 1.95")


def test_missing_calibration_file_raises(tmp_path):
    """Hint: use pytest.raises(FileNotFoundError) around load_calibration(tmp_path / "nope.txt")."""
    todo("expect FileNotFoundError")


def test_malformed_calibration_file_raises(tmp_path):
    """Hint: write 'radius=0.3' and expect ValueError; add match="unexpected key" to be specific."""
    todo("expect ValueError for a wrong key")
