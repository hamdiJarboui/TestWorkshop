"""Lab 2 - pytest: plain asserts, fixtures, parametrization, markers, built-ins.

Run: pytest labs/lab02_pytest -v
"""
import pytest

from autotest.bms import BatteryManagementSystem, BMSFault
from autotest.can import CANFrame, CANMessage, Signal
from autotest.sensors import SensorFault, TemperatureSensor, kmh_to_ms


# ---- 1. plain asserts: pytest rewrites them to show values ---------------------
def test_plain_assert():
    assert kmh_to_ms(72) == pytest.approx(20.0)


def test_approx_for_floats():
    assert 0.1 + 0.2 == pytest.approx(0.3)  # never compare floats with ==


def test_exceptions_with_context():
    with pytest.raises(ValueError, match="above maximum") as info:
        Signal("v", 0, 8, maximum=10).to_raw(11)
    assert "v" in str(info.value)


# ---- 2. parametrization: one test body, many cases -----------------------------
@pytest.mark.parametrize(
    "cells, temp, expected",
    [
        ([3.7, 3.7, 3.7], 25, BMSFault.NONE),
        ([3.7, 4.21, 3.7], 25, BMSFault.OVERVOLTAGE),
        ([3.7, 2.99, 3.7], 25, BMSFault.UNDERVOLTAGE),
        ([3.7, 3.7, 3.7], 61, BMSFault.OVERTEMPERATURE),
        ([3.7, 3.7, 3.7], -21, BMSFault.UNDERTEMPERATURE),
    ],
    ids=["healthy", "overvolt", "undervolt", "overtemp", "undertemp"],
)
def test_bms_fault_detection(cells, temp, expected):
    assert BatteryManagementSystem().evaluate(cells, temp) is expected


@pytest.mark.parametrize("dlc", range(0, 9))
def test_every_legal_dlc(dlc):
    assert CANFrame(0x100, bytes(dlc)).dlc == dlc


# ---- 3. fixtures: setup/teardown with dependency injection ---------------------
class FakeADC:
    def __init__(self, *values):
        self.values = list(values)

    def read(self):
        return self.values.pop(0) if len(self.values) > 1 else self.values[0]


@pytest.fixture
def adc():
    return FakeADC(2048)


@pytest.fixture
def sensor(adc):  # fixtures can use other fixtures
    return TemperatureSensor(adc)


def test_mid_scale_is_about_55_degrees(sensor):
    assert sensor.read() == pytest.approx(55.0, abs=0.05)


@pytest.fixture
def battery():
    bms = BatteryManagementSystem(capacity_ah=50, soc=50)
    yield bms             # everything after yield is teardown
    assert 0 <= bms.soc <= 100, "invariant must hold after EVERY test"


def test_soc_clamped(battery):
    battery.update_soc(1000, 3600)
    assert battery.soc == 100


@pytest.fixture(scope="module")
def engine_message():
    """Module scope: built once, shared (only for immutable objects!)."""
    return CANMessage(0x2F0, "Engine", 4, (Signal("rpm", 0, 16, factor=0.25),))


def test_module_scoped_fixture(engine_message):
    assert engine_message.decode(engine_message.encode({"rpm": 1000}))["rpm"] == 1000


# ---- 4. built-in fixtures ------------------------------------------------------
def test_tmp_path_gives_each_test_a_private_directory(tmp_path):
    log = tmp_path / "trace.asc"
    log.write_text("0.001 1 123 Rx d 3 01 02 03\n")
    assert log.read_text().startswith("0.001")


def test_monkeypatch_environment(monkeypatch):
    import os
    monkeypatch.setenv("VEHICLE_VARIANT", "EV")
    assert os.environ["VEHICLE_VARIANT"] == "EV"  # restored automatically afterwards


def test_capsys_captures_output(capsys):
    print("DTC U0121 set")
    assert "U0121" in capsys.readouterr().out


# ---- 5. markers: select what to run --------------------------------------------
@pytest.mark.smoke
def test_smoke_sensor_rails(sensor, adc):
    adc.values = [0]
    with pytest.raises(SensorFault):
        sensor.read()


@pytest.mark.skipif(not hasattr(pytest, "approx"), reason="needs pytest.approx")
def test_conditional_skip():
    assert True


@pytest.mark.xfail(reason="BUG-114: resolution 0.25 rpm rounds 0.1 rpm to 0", strict=True)
def test_known_bug_is_tracked():
    sig = Signal("rpm", 0, 16, factor=0.25)
    assert sig.to_raw(0.1) == 1
