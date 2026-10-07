"""Lab 5 exercises - integration, fault injection, contract tests.

  Run it:       python course.py exercise 5
  How it works: every test starts with a todo(...) line. DELETE that line when you start on the
                test; the test then passes only if what you wrote is correct.
  Done when:    `python course.py progress` shows every test of Lab 5 passing.

Fixtures from conftest.py: `bus` (VirtualCANBus) and `clock` (FakeClock).
Useful: bus.add_fault(hook) installs a function  hook(frame) -> frame | None  (None = drop the frame);
        bus.clear_faults();  bus.log = list of every frame sent.
"""
import random

from autotest.bus import VirtualCANBus
from autotest.can import CANFrame, E2EStatus, e2e_check
from autotest.ecu import WHEEL_SPEED_MSG, InstrumentCluster, WheelSpeedECU
from autotest.learn import todo


class DataLogger:
    """A third node on the bus: records the speed of every frame that passes the CRC check."""

    def __init__(self, bus):
        self.speeds = []
        # TODO: subscribe self._rx to the bus, only for frame id WHEEL_SPEED_MSG.frame_id  (bus.subscribe(listener, ids={...}))

    def _rx(self, frame):
        # TODO: status, payload = e2e_check(frame.data);  if OK: decode with WHEEL_SPEED_MSG.decode(payload)["speed_kmh"]
        pass


def test_logger_sees_what_cluster_sees(bus, clock):
    """Exercise 1. First complete DataLogger above. Then: send 10, send 20 with a corrupted CRC byte, send 30.
    The logger must record exactly [10.0, 30.0] and the cluster must show "30".

    Hint 1: corrupt like this:  bus.add_fault(lambda f: CANFrame(f.arbitration_id, bytes([f.data[0] ^ 0xFF]) + f.data[1:]))
    Hint 2: remove the fault again with bus.clear_faults() before sending 30.
    """
    todo("complete DataLogger, then write the scenario")


def test_cluster_never_displays_invented_speed(bus, clock):
    """Exercise 2. A fault hook flips ONE random bit in 1 of every 5 frames (use random.Random(42) so it is repeatable).
    Send 100 frames. Whatever the cluster shows must be a speed that was actually SENT (or "--").

    Hint 1: rng = random.Random(42);  in the hook:  if rng.randrange(5) == 0: copy data to a bytearray, flip one bit, return a new CANFrame
    Hint 2: keep a set `sent` of the strings you sent (str(speed));  after each send assert  shown in sent | {"--"}
    """
    todo("write the random-corruption test")


def test_wheel_speed_contract():
    """Exercise 3 - a CONTRACT test: pin the exact bytes on the wire so nobody changes the scale factor unnoticed.

    Hint 1: bus = VirtualCANBus();  WheelSpeedECU(bus).send_speed(100.0);  look at bus.log[0].data
    Hint 2: print(bus.log[0].data.hex()) once and CHECK it by hand against the spec (CRC, counter, speed 100.00 km/h = raw 10000
            little-endian, valid flag) BEFORE you paste it as the expected value - otherwise you only freeze whatever the code does.
    Hint 3: also assert the frame id is 0x1A0.
    """
    todo("assert the exact bytes of a 100.0 km/h frame")
