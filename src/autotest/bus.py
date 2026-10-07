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
        self.log.append(frame)
        current: Optional[CANFrame] = frame
        for hook in self._fault_hooks:
            current = hook(current)  # type: ignore[arg-type]
            if current is None:
                return False
        for listener, ids in self._listeners:
            if ids is None or current.arbitration_id in ids:
                listener(current)
        return True
