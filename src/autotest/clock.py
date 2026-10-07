"""Injectable clocks: production code takes a clock, tests pass a FakeClock."""
import time


class SystemClock:
    def now(self) -> float:
        return time.monotonic()


class FakeClock:
    """Deterministic clock - the key trick for testing timeouts without sleeping."""

    def __init__(self, start: float = 0.0):
        self._t = start

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("time cannot go backwards")
        self._t += seconds
