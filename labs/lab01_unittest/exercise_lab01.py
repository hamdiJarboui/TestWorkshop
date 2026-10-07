"""Lab 1 exercises - unit tests with unittest.

  Run it:       python course.py exercise 1
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the
                test; the test then passes only if what you wrote is correct.
  Done when:    `python course.py progress` shows every test of Lab 1 passing.
  Stuck?        Read the hints in the docstring ONE AT A TIME; the last hint of some tests gives the answer.
"""
import unittest

from autotest.bms import BatteryManagementSystem
from autotest.can import CANMessage, E2EStatus, Signal, e2e_check, e2e_protect
from autotest.learn import todo


class TestCoulombCounting(unittest.TestCase):
    """Exercise 1 - BatteryManagementSystem.update_soc(current_a, dt_s) integrates current into SOC.

    SOC change in percentage points = current * time / 3600 / capacity * 100   (capacity in Ah)
    """

    def setUp(self):
        self.bms = BatteryManagementSystem(capacity_ah=50.0, soc=50.0)      # a 50 Ah pack at 50 %

    def test_charging_is_clamped_at_100(self):
        """50 A for one hour would add +100 points (50 + 100 = 150) but SOC can never exceed 100.

        Hint 1: update_soc returns the new SOC:   new_soc = self.bms.update_soc(50, 3600)
        Hint 2: use self.assertEqual(new_soc, ...) with the value the SPECIFICATION demands.
        """
        todo("charge 50 A for 3600 s and expect SOC 100")

    def test_half_capacity_for_one_hour_adds_exactly_50_points(self):
        """Start from 0 %: 25 A for one hour on a 50 Ah pack is half the capacity.

        Hint 1: set up the start state first:   self.bms.soc = 0
        Hint 2: floats! use self.assertAlmostEqual(actual, expected)
        """
        todo("expect 50.0 after 25 A for 3600 s starting at 0 %")

    def test_discharge_never_goes_below_zero(self):
        """Hint: a large negative current (discharging), e.g. -50 A for 7200 s, must stop at 0 %."""
        todo("expect 0.0")

    def test_negative_dt_is_rejected(self):
        """Time cannot run backwards: update_soc(10, -1) must raise ValueError.

        Hint: with self.assertRaises(ValueError):  <call goes here>
        """
        todo("use assertRaises")


class TestCanMessageCodec(unittest.TestCase):
    """Exercise 2 - a two-signal message. physical = raw * factor + offset;  signals are packed little-endian."""

    def setUp(self):
        self.msg = CANMessage(0x2F0, "Engine", 4, (
            Signal("rpm", 0, 16, factor=0.25),          # bits 0..15,  0.25 rpm per step
            Signal("coolant", 16, 8, offset=-40),       # bits 16..23, -40 degC offset
        ))

    def test_encode_known_bytes(self):
        """Encode rpm=3000, coolant=90 and compare with the bytes you computed BY HAND first.

        Hint 1: raw = (physical - offset) / factor   ->   rpm raw = ?   coolant raw = ?
        Hint 2: write the raw numbers in hex; little-endian puts the LOW byte first; the 4th byte is padding (0).
        Hint 3 (spoiler): rpm 12000 = 0x2EE0, coolant 130 = 0x82   ->   bytes([0xE0, 0x2E, 0x82, 0x00])
        Call:  self.msg.encode({"rpm": 3000, "coolant": 90})
        """
        todo("compare encode(...) with your hand-computed bytes")

    def test_round_trip_for_several_operating_points(self):
        """decode(encode(x)) must give x back. Use subTest so one failing point does not hide the others.

        Hint 1: for rpm, coolant in [(0, -40), (800, 20), (6500.25, 90)]:
                    with self.subTest(rpm=rpm, coolant=coolant):  ...
        Hint 2: self.assertEqual(self.msg.decode(self.msg.encode(values)), values)
        """
        todo("round trip with subTest")

    def test_unknown_signal_name(self):
        """encode() with a signal that is not in the message must raise an error.

        Hint: find out WHICH exception type by reading CANMessage.encode in src/autotest/can.py
              (or try it in a Python shell), then use assertRaises with exactly that type.
        """
        todo("assertRaises for an unknown signal")

    def test_decode_wrong_length(self):
        """decode() of a 2-byte payload for a 4-byte message must raise ValueError."""
        todo("assertRaises(ValueError)")


class TestE2E(unittest.TestCase):
    """Exercise 3 - end-to-end protection: e2e_protect(payload, counter) / e2e_check(data, expected_counter)."""

    def test_protect_then_check_is_ok(self):
        """Hint: status, payload = e2e_check(e2e_protect(b"\\x01\\x02", 5), 5)  -> status is E2EStatus.OK, payload is b"\\x01\\x02"."""
        todo("round trip, check status AND payload")

    def test_corrupted_payload_is_detected(self):
        """Flip one bit of the last byte after protecting; the status must be E2EStatus.CRC_ERROR.

        Hint: protected = bytearray(e2e_protect(b"\\x01\\x02", 5));  protected[-1] ^= 0x01;  e2e_check(bytes(protected))
        """
        todo("flip a bit, expect CRC_ERROR")

    def test_counter_wraps_at_16(self):
        """The alive counter is 4 bits wide, so counter 16 behaves like counter 0.

        Hint: compare e2e_protect(b"x", 16) with e2e_protect(b"x", 0).
        """
        todo("counter 16 == counter 0")


if __name__ == "__main__":
    unittest.main()
