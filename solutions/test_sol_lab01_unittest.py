"""Solutions - Lab 1 (unittest)."""
import unittest

from autotest.bms import BatteryManagementSystem
from autotest.can import CANMessage, E2EStatus, Signal, e2e_check, e2e_protect


class TestCoulombCounting(unittest.TestCase):
    def setUp(self):
        self.bms = BatteryManagementSystem(capacity_ah=50.0, soc=50.0)

    def test_charging_is_clamped_at_100(self):
        # 50 A for one hour into a 50 Ah pack = +100 % -> 150 % raw, clamped
        self.assertEqual(self.bms.update_soc(50, 3600), 100.0)

    def test_half_capacity_for_one_hour_adds_exactly_50_percent_points(self):
        self.bms.soc = 0
        self.assertAlmostEqual(self.bms.update_soc(25, 3600), 50.0)

    def test_discharge_never_goes_below_zero(self):
        self.assertEqual(self.bms.update_soc(-50, 7200), 0.0)

    def test_negative_dt_is_rejected(self):
        with self.assertRaises(ValueError):
            self.bms.update_soc(10, -1)


class TestCanMessageCodec(unittest.TestCase):
    def setUp(self):
        self.msg = CANMessage(0x2F0, "Engine", 4, (
            Signal("rpm", 0, 16, factor=0.25),
            Signal("coolant", 16, 8, offset=-40),
        ))

    def test_encode_known_bytes(self):
        # rpm 3000 / 0.25 = 12000 = 0x2EE0 -> E0 2E ; coolant (90+40) = 130 = 0x82 ; pad 00
        self.assertEqual(self.msg.encode({"rpm": 3000, "coolant": 90}), bytes([0xE0, 0x2E, 0x82, 0x00]))

    def test_round_trip_for_several_operating_points(self):
        for rpm, coolant in [(0, -40), (800, 20), (6500.25, 90), (16383.75, 215)]:
            with self.subTest(rpm=rpm, coolant=coolant):
                out = self.msg.decode(self.msg.encode({"rpm": rpm, "coolant": coolant}))
                self.assertEqual(out, {"rpm": rpm, "coolant": coolant})

    def test_unknown_signal_name(self):
        with self.assertRaises(KeyError):
            self.msg.encode({"torque": 1})

    def test_decode_wrong_length(self):
        with self.assertRaises(ValueError):
            self.msg.decode(b"\x00\x00")


class TestE2E(unittest.TestCase):
    def test_protect_then_check_is_ok(self):
        status, payload = e2e_check(e2e_protect(b"\x01\x02", 5), 5)
        self.assertIs(status, E2EStatus.OK)
        self.assertEqual(payload, b"\x01\x02")

    def test_corrupted_payload_is_detected(self):
        data = bytearray(e2e_protect(b"\x01\x02", 5))
        data[-1] ^= 0x01
        self.assertIs(e2e_check(bytes(data))[0], E2EStatus.CRC_ERROR)

    def test_counter_wraps_at_16(self):
        self.assertEqual(e2e_protect(b"x", 16), e2e_protect(b"x", 0))

    def test_wrong_counter_is_reported_separately_from_crc(self):
        self.assertIs(e2e_check(e2e_protect(b"x", 3), 4)[0], E2EStatus.COUNTER_ERROR)

    def test_too_short(self):
        self.assertIs(e2e_check(b"\x00")[0], E2EStatus.TOO_SHORT)


if __name__ == "__main__":
    unittest.main()
