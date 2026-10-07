"""Lab 11 exercises. Run: pytest labs/lab11_sil_simulation/exercise_lab11.py -v"""
import pytest


# Exercise 1 - Write acceptance criteria as numbers: "dip <= 4 km/h and recovery within 20 s" for a
# 8 % hill. Run the simulation. Does the default controller (kp=0.05, ki=0.01) pass?
# If not, tune kp/ki (write the sweep as a parametrized test) and state your choice.
def test_8_percent_hill():
    pytest.fail("TODO")


# Exercise 2 - Low-friction surface: change tyre_mu's peak to 0.3 (monkeypatch). With ABS the
# stopping distance must be < locked-wheel distance. Does the 10 % improvement still hold?
def test_ice():
    pytest.fail("TODO")


# Exercise 3 - Sensor-fault in the loop: feed the controller a speed that is 5 km/h too low
# (miscalibrated wheel sensor). Predict, then measure, the steady-state ERROR of the real car.
# Which requirement/diagnostic would catch this in the field?
def test_biased_speed_sensor():
    pytest.fail("TODO")
