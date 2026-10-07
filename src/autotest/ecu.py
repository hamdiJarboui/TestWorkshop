"""Two cooperating ECUs: a wheel-speed sender and an instrument cluster receiver.

On the wire a wheel-speed frame (id 0x1A0) is 5 bytes:

    byte 0     byte 1          bytes 2-4
    CRC-8      alive counter   payload: speed (16 bit, 0.01 km/h) + valid flag (1 bit)
"""
from __future__ import annotations

from .bus import VirtualCANBus
from .can import CANFrame, CANMessage, E2EStatus, Signal, e2e_check, e2e_protect
from .clock import FakeClock, SystemClock
from .diagnostics import DiagnosticManager

WHEEL_SPEED_MSG = CANMessage(
    frame_id=0x1A0,
    name="WheelSpeed",
    dlc=3,
    signals=(
        Signal("speed_kmh", 0, 16, factor=0.01, minimum=0.0, maximum=300.0),
        Signal("valid", 16, 1),
    ),
)

DTC_COMM_LOST = "U0121"
DTC_E2E_FAIL = "U0100"


class WheelSpeedECU:
    def __init__(self, bus: VirtualCANBus):
        self.bus = bus
        self._counter = 0

    def send_speed(self, speed_kmh: float) -> bool:
        payload = WHEEL_SPEED_MSG.encode({"speed_kmh": speed_kmh, "valid": 1})
        data = e2e_protect(payload, self._counter)
        self._counter = (self._counter + 1) & 0x0F
        return self.bus.send(CANFrame(WHEEL_SPEED_MSG.frame_id, data))


class InstrumentCluster:
    TIMEOUT_S = 0.1

    def __init__(self, bus: VirtualCANBus, clock: FakeClock | SystemClock | None = None,
                 diag: DiagnosticManager | None = None):
        self.clock = clock or SystemClock()
        self.diag = diag or DiagnosticManager(fail_threshold=2)
        self._speed: float | None = None
        self._last_rx = self.clock.now()
        self._expected_counter: int | None = None
        bus.subscribe(self._on_frame, ids={WHEEL_SPEED_MSG.frame_id})

    def _on_frame(self, frame: CANFrame) -> None:
        status, payload = e2e_check(frame.data, self._expected_counter)
        if status is not E2EStatus.OK:
            self.diag.report(DTC_E2E_FAIL, failed=True)
            if status is E2EStatus.COUNTER_ERROR:  # resynchronise after a lost frame
                self._expected_counter = (frame.data[1] + 1) & 0x0F
            elif self._expected_counter is not None:
                # BUG-130: a corrupted frame still occupies one slot in the sequence, so the
                # next good frame must not be rejected as a counter error as well.
                self._expected_counter = (self._expected_counter + 1) & 0x0F
            return
        self.diag.report(DTC_E2E_FAIL, failed=False)
        signals = WHEEL_SPEED_MSG.decode(payload)
        self._speed = signals["speed_kmh"] if signals["valid"] else None
        self._last_rx = self.clock.now()
        self._expected_counter = (frame.data[1] + 1) & 0x0F

    def displayed_speed(self) -> str:
        """What the driver sees: the speed, or "--" when it is unknown or stale.

        Call this once per display cycle. It also *supervises* the bus: every call checks the
        100 ms timeout and reports the result to diagnostics, so it is not a pure getter.
        """
        if self.clock.now() - self._last_rx > self.TIMEOUT_S:
            self.diag.report(DTC_COMM_LOST, failed=True)
            return "--"
        self.diag.report(DTC_COMM_LOST, failed=False)
        return "--" if self._speed is None else f"{self._speed:.0f}"
