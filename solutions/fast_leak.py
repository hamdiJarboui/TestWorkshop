"""Solution module for Lab 10: LeakDetector with O(1) amortised cost per sample."""
from collections import deque


class FastLeakDetector:
    WINDOW_S = 60.0
    DROP_KPA = 20.0

    def __init__(self):
        self._window = deque()      # (t, kpa) with kpa strictly decreasing -> front is the maximum

    def add(self, t, kpa):
        while self._window and self._window[-1][1] <= kpa:
            self._window.pop()
        self._window.append((t, kpa))
        while t - self._window[0][0] > self.WINDOW_S:
            self._window.popleft()
        return self._window[0][1] - kpa >= self.DROP_KPA
