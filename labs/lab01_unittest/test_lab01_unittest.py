"""Lab 1 - unit testing with the standard library's unittest.

Run:  python -m unittest discover -s labs/lab01_unittest -p "test_lab01*.py" -v
  or: pytest labs/lab01_unittest -v      (pytest runs unittest tests too)
"""
import dataclasses
import unittest

from autotest.can import CANFrame, Signal, crc8
from autotest.sensors import celsius_to_fahrenheit, kmh_to_ms, ms_to_kmh, wheel_speed_kmh


class TestUnitConversions(unittest.TestCase):
    """Anatomy of a test: Arrange - Act - Assert."""

    def test_kmh_to_ms_known_value(self):
        self.assertAlmostEqual(kmh_to_ms(36.0), 10.0)

    def test_round_trip(self):
        for kmh in (0, 1, 50, 130.5):
            with self.subTest(kmh=kmh):  # one failure does not hide the others
                self.assertAlmostEqual(ms_to_kmh(kmh_to_ms(kmh)), kmh)

    def test_freezing_point(self):
        self.assertEqual(celsius_to_fahrenheit(0), 32)

    def test_wheel_speed_formula(self):
        # 40 pulses / 20 per rev = 2 rev in 1 s; 2 m circumference -> 4 m/s = 14.4 km/h
        self.assertAlmostEqual(wheel_speed_kmh(40, 20, 2.0, 1.0), 14.4)

    def test_invalid_interval_raises(self):
        with self.assertRaises(ValueError):
            wheel_speed_kmh(10, 20, 2.0, 0)

    def test_error_message_is_helpful(self):
        with self.assertRaisesRegex(ValueError, "invalid wheel speed"):
            wheel_speed_kmh(-1, 20, 2.0, 1.0)


class TestCrc8(unittest.TestCase):
    def test_standard_check_value(self):
        # CRC-8/SAE-J1850 catalogue check value for ASCII "123456789"
        self.assertEqual(crc8(b"123456789"), 0x4B)

    def test_detects_single_bit_flip(self):
        good = bytes([0x12, 0x34, 0x56])
        for bit in range(24):
            with self.subTest(bit=bit):
                bad = bytearray(good)
                bad[bit // 8] ^= 1 << (bit % 8)
                self.assertNotEqual(crc8(good), crc8(bytes(bad)))


class TestCANFrame(unittest.TestCase):
    """Fixtures: setUp runs before EVERY test, so tests never share state."""

    def setUp(self):
        self.frame = CANFrame(0x123, b"\x01\x02\x03")

    def tearDown(self):
        pass  # release files / sockets here; nothing needed for pure objects

    def test_dlc_is_data_length(self):
        self.assertEqual(self.frame.dlc, 3)

    def test_frame_is_immutable(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):   # name the EXACT exception, not Exception
            self.frame.arbitration_id = 0x7FF

    def test_standard_id_limit(self):
        CANFrame(0x7FF)  # last legal id: must not raise
        with self.assertRaises(ValueError):
            CANFrame(0x800)

    def test_extended_id_accepts_29_bits(self):
        self.assertEqual(CANFrame(0x1FFFFFFF, is_extended=True).arbitration_id, 0x1FFFFFFF)

    def test_too_many_bytes(self):
        with self.assertRaises(ValueError):
            CANFrame(0x1, bytes(9))


class TestSignalScaling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):  # expensive shared setup, done once per class
        cls.rpm = Signal("rpm", 0, 16, factor=0.25, minimum=0, maximum=16000)

    def test_scaling(self):
        self.assertEqual(self.rpm.to_raw(3000), 12000)
        self.assertEqual(self.rpm.to_physical(12000), 3000)

    def test_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            self.rpm.to_raw(16001)

    @unittest.skip("demonstration: skipped tests are reported, never silently lost")
    def test_skipped(self):
        self.fail("never runs")

    @unittest.expectedFailure
    def test_known_bug_documented(self):
        # An expected failure documents a KNOWN defect; it turns red when the bug is fixed.
        self.assertEqual(self.rpm.to_raw(0.1), 1)  # rounds to 0 - resolution is 0.25 rpm


def load_tests(loader, tests, pattern):
    """Optional hook: build a suite by hand (see README, section 'Suites and runners')."""
    suite = unittest.TestSuite()
    for case in (TestUnitConversions, TestCrc8, TestCANFrame, TestSignalScaling):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
