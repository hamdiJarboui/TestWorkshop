"""Lab 13 exercises - requirements-driven testing, acceptance scenarios, SIL/HIL back-ends.

  Run it:       python course.py exercise 13
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the test.
  Done when:    `python course.py progress` shows every test of Lab 13 passing.
"""
import pytest

from autotest.ecu import InstrumentCluster, WheelSpeedECU
from autotest.learn import todo
from autotest.sensors import TemperatureSensor
from autotest.tpms import LeakDetector, TyreStatus, classify


# --------------------------------------------------------------------------------------------------
# Exercise 1 - REQUIREMENTS-DRIVEN development.
#   docs/requirements.csv already lists REQ-TPMS-001 and REQ-TPMS-002, but (without the instructor's solutions folder)
#   nothing verifies them: the meta-test `test_every_requirement_is_verified_by_at_least_one_test` is RED.
#   Make it green by writing verifying tests that carry the requirement marker.
# --------------------------------------------------------------------------------------------------
@pytest.mark.requirement("REQ-TPMS-001")
def test_critical_pressure_is_classified_critical():
    """REQ-TPMS-001: a tyre below 60 % of nominal (230 kPa), normalised to 20 degC, is CRITICAL.
    Hint 1: 60 % of 230 is 138 kPa. Test just below (137.99), on (138.0 -> LOW, not CRITICAL!) and a clearly critical value (0).
    Hint 2: classify(kpa, temp_c) returns a TyreStatus;  compare with `is`.
    """
    todo("verify REQ-TPMS-001")


@pytest.mark.requirement("REQ-TPMS-002")
def test_a_pressure_drop_of_20_kpa_raises_the_leak_alarm():
    """REQ-TPMS-002: a drop of 20 kPa or more within 60 s raises a rapid-loss alarm.
    Hint 1: leak = LeakDetector();  leak.add(0, 230)  records a sample at t = 0 s;  leak.add(10, 210) returns True/False.
    Hint 2: test exactly 20 kPa (alarm) and 19.99 kPa (no alarm).
    """
    todo("verify REQ-TPMS-002")


# Bonus (terminal): add a line REQ-TPMS-003 (sensor-id validation) to docs/requirements.csv, watch the meta-test go red again,
# then write the verifying test and watch it turn green.


# --------------------------------------------------------------------------------------------------
# Exercise 2 - an acceptance scenario in Given / When / Then style.
# --------------------------------------------------------------------------------------------------
@pytest.mark.requirement("REQ-CLU-001")
def test_dashboard_never_goes_backwards_during_acceleration(bus, clock):
    """Given the bus is healthy
       When  the car accelerates from 0 to 100 km/h in ten steps of 10 km/h (one frame every 10 ms)
       Then  the displayed speed never decreases.

    Hint 1: ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)
    Hint 2: collect int(cluster.displayed_speed()) after each send_speed(...) and clock.advance(0.01)
    Hint 3: assert shown == sorted(shown)
    """
    todo("write the scenario with Given/When/Then comments")


# --------------------------------------------------------------------------------------------------
# Exercise 3 - one test body, two back-ends (simulator now, hardware later).
# --------------------------------------------------------------------------------------------------
class SimulatedADC:
    def read(self):
        return 2048


@pytest.fixture(params=["virtual", "pcan"])
def adc_backend(request):
    """Return an ADC for the requested back-end. 'pcan' stands for a real bench adapter: skip it when no hardware is connected.

    Hint 1: if request.param == "pcan": pytest.skip("no hardware bench connected")
    Hint 2: otherwise return SimulatedADC()
    """
    todo("implement the fixture so the hardware variant is skipped")


def test_mid_scale_temperature_is_plausible_on_every_back_end(adc_backend):
    """Hint: the same assertion for both back-ends:  -40 < TemperatureSensor(adc_backend).read() < 150
    Run it: you should see one pass and one SKIPPED (with the reason)."""
    todo("write the shared assertion")
