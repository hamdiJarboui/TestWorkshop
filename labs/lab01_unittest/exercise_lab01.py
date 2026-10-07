"""Lab 1 exercises - complete every TODO, then run:
    pytest labs/lab01_unittest/exercise_lab01.py -v
"""
import unittest

from autotest.can import CANMessage, Signal, e2e_check, e2e_protect, E2EStatus
from autotest.bms import BatteryManagementSystem


class TestCoulombCounting(unittest.TestCase):
    """Exercise 1: test BatteryManagementSystem.update_soc."""

    def setUp(self):
        self.bms = BatteryManagementSystem(capacity_ah=50.0, soc=50.0)

    def test_charging_one_hour_at_capacity_current_adds_100_percent_but_is_clamped(self):
        self.fail("TODO: charge 50 A for 3600 s; expect SOC clamped to 100")

    def test_discharge_never_goes_below_zero(self):
        self.fail("TODO")

    def test_negative_dt_is_rejected(self):
        self.fail("TODO: use assertRaises")


class TestCanMessageCodec(unittest.TestCase):
    """Exercise 2: a two-signal message. Write at least three tests (use subTest)."""

    def setUp(self):
        self.msg = CANMessage(0x2F0, "Engine", 4, (
            Signal("rpm", 0, 16, factor=0.25),
            Signal("coolant", 16, 8, offset=-40),
        ))

    def test_encode_known_bytes(self):
        self.fail("TODO: rpm=3000, coolant=90 -> bytes? (work it out by hand first!)")

    def test_unknown_signal_name(self):
        self.fail("TODO: which exception type does encode() raise?")

    def test_decode_wrong_length(self):
        self.fail("TODO")


class TestE2E(unittest.TestCase):
    """Exercise 3: end-to-end protection."""

    def test_protect_then_check_is_ok(self):
        self.fail("TODO")

    def test_corrupted_payload_is_detected(self):
        self.fail("TODO: flip a bit, expect E2EStatus.CRC_ERROR")

    def test_counter_wraps_at_16(self):
        self.fail("TODO: counter 16 behaves like counter 0")


if __name__ == "__main__":
    unittest.main()
