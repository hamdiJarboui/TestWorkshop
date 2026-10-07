"""Lab 5 exercises. Run: pytest labs/lab05_integration/exercise_lab05.py -v"""
import pytest

from autotest.ecu import InstrumentCluster, WheelSpeedECU


# Exercise 1 - Top-down vs bottom-up: add a THIRD node (write a tiny `DataLogger` class in this
# file that subscribes to the bus and stores decoded speeds). Integrate it and assert it sees
# exactly the frames the cluster accepted.
def test_logger_sees_what_cluster_sees(bus, clock):
    pytest.fail("TODO")


# Exercise 2 - Fault injection on the bus: a hook that flips ONE random-but-seeded bit
# in 1 of every 5 frames (use random.Random(42)). Send 100 frames. Assert the cluster
# never displays a value that was not sent.
def test_cluster_never_displays_invented_speed(bus, clock):
    pytest.fail("TODO")


# Exercise 3 - Interface contract: write a test that FAILS if someone changes the scale factor
# of WHEEL_SPEED_MSG without updating the receiver. (Hint: compare against raw bytes
# captured on the wire - a 'contract test'.)
def test_wheel_speed_contract():
    pytest.fail("TODO")
