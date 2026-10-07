"""Lab 5 - integration testing: WheelSpeedECU -> VirtualCANBus -> InstrumentCluster.

Unit tests prove each part works alone; these prove the parts agree on the INTERFACE:
byte layout, scaling, E2E protection, alive counter and timing.
"""
import pytest

from autotest.can import CANFrame
from autotest.ecu import (
    DTC_COMM_LOST, DTC_E2E_FAIL, InstrumentCluster, WheelSpeedECU,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def ecu(bus):
    return WheelSpeedECU(bus)


@pytest.fixture
def cluster(bus, clock):
    return InstrumentCluster(bus, clock)


@pytest.mark.smoke
def test_speed_travels_from_sensor_ecu_to_display(ecu, cluster):
    ecu.send_speed(87.4)
    assert cluster.displayed_speed() == "87"


@pytest.mark.parametrize("speed", [0, 0.01, 50, 130.55, 299.99])
def test_interface_scaling_agrees_end_to_end(ecu, cluster, speed):
    ecu.send_speed(speed)
    assert cluster.displayed_speed() == f"{speed:.0f}"


def test_frame_on_the_wire_matches_the_interface_specification(ecu, bus):
    ecu.send_speed(100.0)
    frame = bus.log[0]
    assert frame.arbitration_id == 0x1A0
    assert frame.dlc == 5                        # crc + counter + 3 payload bytes
    assert frame.data[2:4] == (10000).to_bytes(2, "little")  # 100.00 km/h, factor 0.01


@pytest.mark.requirement("REQ-CLU-001")
def test_cluster_blanks_after_100ms_without_frames(ecu, cluster, clock):
    ecu.send_speed(60)
    clock.advance(0.099)
    assert cluster.displayed_speed() == "60"
    clock.advance(0.002)                         # total 101 ms
    assert cluster.displayed_speed() == "--"


@pytest.mark.requirement("REQ-CLU-001")
def test_cluster_recovers_when_frames_return(ecu, cluster, clock):
    ecu.send_speed(60)
    clock.advance(1)
    assert cluster.displayed_speed() == "--"
    ecu.send_speed(70)
    assert cluster.displayed_speed() == "70"


@pytest.mark.requirement("REQ-CAN-003")
def test_corrupted_frame_is_rejected_and_last_good_value_kept(ecu, cluster, bus):
    ecu.send_speed(50)
    bus.add_fault(lambda f: CANFrame(f.arbitration_id, bytes([f.data[0] ^ 0xFF]) + f.data[1:]))
    ecu.send_speed(120)                          # CRC byte corrupted in flight
    assert cluster.displayed_speed() == "50"
    assert cluster.diag.stored_codes() == []     # one failure is only debounced...
    ecu.send_speed(121)
    assert cluster.diag.stored_codes() == [DTC_E2E_FAIL]  # ...two confirm the DTC


@pytest.mark.requirement("REQ-CAN-003")
def test_lost_frame_is_detected_by_alive_counter_and_cluster_resyncs(ecu, cluster, bus):
    ecu.send_speed(10)
    bus.add_fault(lambda f: None)                # bus drops one frame
    ecu.send_speed(20)
    bus.clear_faults()
    ecu.send_speed(30)                           # counter jumped by 2 -> rejected once
    assert cluster.displayed_speed() == "10"
    ecu.send_speed(40)                           # resynchronised -> accepted
    assert cluster.displayed_speed() == "40"


def test_cluster_ignores_other_message_ids(ecu, cluster, bus):
    ecu.send_speed(33)
    bus.send(CANFrame(0x7FF, b"\xFF" * 8))       # unrelated traffic
    assert cluster.displayed_speed() == "33"


def test_comm_lost_dtc_is_confirmed_by_debounce(cluster, clock):
    clock.advance(1)
    cluster.displayed_speed()
    assert cluster.diag.active_codes() == []     # first miss: only counted
    cluster.displayed_speed()
    assert cluster.diag.active_codes() == [DTC_COMM_LOST]


def test_bus_log_contains_every_frame_even_when_dropped(ecu, bus):
    bus.add_fault(lambda f: None)
    assert ecu.send_speed(10) is False
    assert len(bus.log) == 1
