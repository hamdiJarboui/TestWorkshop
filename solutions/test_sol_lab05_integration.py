"""Solutions - Lab 5 (integration)."""
import random

import pytest

from autotest.can import CANFrame, E2EStatus, e2e_check
from autotest.ecu import WHEEL_SPEED_MSG, InstrumentCluster, WheelSpeedECU

pytestmark = pytest.mark.integration


class DataLogger:
    def __init__(self, bus):
        self.speeds = []
        bus.subscribe(self._rx, ids={WHEEL_SPEED_MSG.frame_id})

    def _rx(self, frame):
        status, payload = e2e_check(frame.data)
        if status is E2EStatus.OK:
            self.speeds.append(WHEEL_SPEED_MSG.decode(payload)["speed_kmh"])


def test_logger_sees_what_cluster_sees(bus, clock):
    logger, cluster, ecu = DataLogger(bus), InstrumentCluster(bus, clock), WheelSpeedECU(bus)
    ecu.send_speed(10)
    bus.add_fault(lambda f: CANFrame(f.arbitration_id, bytes([f.data[0] ^ 0xFF]) + f.data[1:]))
    ecu.send_speed(20)
    bus.clear_faults()
    ecu.send_speed(30)
    assert logger.speeds == [10.0, 30.0]
    assert cluster.displayed_speed() == "30"


def test_cluster_never_displays_invented_speed(bus, clock):
    rng = random.Random(42)
    ecu, cluster = WheelSpeedECU(bus), InstrumentCluster(bus, clock)
    sent = set()

    def hook(frame):
        if rng.randrange(5) == 0:
            data = bytearray(frame.data)
            data[rng.randrange(len(data))] ^= 1 << rng.randrange(8)
            return CANFrame(frame.arbitration_id, bytes(data))
        return frame

    bus.add_fault(hook)
    for i in range(100):
        speed = (i * 7) % 250
        sent.add(str(speed))
        ecu.send_speed(speed)
        assert cluster.displayed_speed() in sent | {"--"}


def test_wheel_speed_contract():
    """Contract test: the exact bytes on the wire are part of the interface specification.
    If someone changes factor/offset/layout this fails BEFORE the receiver team notices."""
    from autotest.bus import VirtualCANBus
    bus = VirtualCANBus()
    WheelSpeedECU(bus).send_speed(100.0)
    assert bus.log[0].data.hex() == "d000102701"       # crc=d0 counter=00 speed=0x2710 valid=1
    assert WHEEL_SPEED_MSG.signals[0].factor == 0.01
