"""A virtual CAN bus with fault-injection hooks, used for integration tests."""
from __future__ import annotations

from typing import Callable, Optional

from .can import CANFrame

Listener = Callable[[CANFrame], None]
FaultHook = Callable[[CANFrame], Optional[CANFrame]]


class VirtualCANBus:
    def __init__(self) -> None:
        self._listeners: list[tuple[Listener, Optional[set[int]]]] = []
        self._fault_hooks: list[FaultHook] = []
        self.log: list[CANFrame] = []

    def subscribe(self, listener: Listener, ids: set[int] | None = None) -> None:
        self._listeners.append((listener, ids))

    def add_fault(self, hook: FaultHook) -> None:
        """A hook may return a modified frame, or None to drop it."""
        self._fault_hooks.append(hook)

    def clear_faults(self) -> None:
        self._fault_hooks.clear()

    def send(self, frame: CANFrame) -> bool:
        """Put a frame on the bus. Returns False if a fault hook dropped it. Always logs the ORIGINAL frame."""
        self.log.append(frame)
        delivered = frame
        for hook in self._fault_hooks:         # each hook may corrupt the frame or drop it
            result = hook(delivered)
            if result is None:
                return False                # frame lost on the bus: nobody receives it
            delivered = result
        for listener, ids in self._listeners:
            if ids is None or delivered.arbitration_id in ids:
                listener(delivered)
        return True
