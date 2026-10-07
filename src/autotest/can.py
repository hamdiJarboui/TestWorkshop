"""CAN frames, signal packing and end-to-end (E2E) protection."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field


class E2EStatus(enum.Enum):
    OK = "ok"
    TOO_SHORT = "too_short"
    CRC_ERROR = "crc_error"
    COUNTER_ERROR = "counter_error"


def crc8(data: bytes, poly: int = 0x1D, init: int = 0xFF, xor_out: int = 0xFF) -> int:
    """CRC-8 SAE J1850 (the AUTOSAR E2E profile 1 polynomial)."""
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc ^ xor_out


@dataclass(frozen=True)
class CANFrame:
    arbitration_id: int
    data: bytes = b""
    is_extended: bool = False

    def __post_init__(self) -> None:
        limit = 0x1FFFFFFF if self.is_extended else 0x7FF
        if not 0 <= self.arbitration_id <= limit:
            raise ValueError(f"arbitration id 0x{self.arbitration_id:X} out of range")
        if len(self.data) > 8:
            raise ValueError("classic CAN carries at most 8 data bytes")

    @property
    def dlc(self) -> int:
        return len(self.data)


@dataclass(frozen=True)
class Signal:
    """A physical value packed into a frame (Intel / little-endian bit order)."""

    name: str
    start_bit: int
    length: int
    factor: float = 1.0
    offset: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    signed: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.length <= 64 or self.start_bit < 0:
            raise ValueError("invalid signal geometry")
        if self.factor == 0:
            raise ValueError("factor must not be zero")

    def raw_range(self) -> tuple[int, int]:
        if self.signed:
            return -(1 << (self.length - 1)), (1 << (self.length - 1)) - 1
        return 0, (1 << self.length) - 1

    def to_raw(self, physical: float) -> int:
        if self.minimum is not None and physical < self.minimum:
            raise ValueError(f"{self.name}: {physical} below minimum {self.minimum}")
        if self.maximum is not None and physical > self.maximum:
            raise ValueError(f"{self.name}: {physical} above maximum {self.maximum}")
        raw = round((physical - self.offset) / self.factor)
        low, high = self.raw_range()
        if not low <= raw <= high:
            raise ValueError(f"{self.name}: raw value {raw} does not fit {self.length} bits")
        return raw

    def to_physical(self, raw: int) -> float:
        return raw * self.factor + self.offset


@dataclass(frozen=True)
class CANMessage:
    """Message definition: a frame id, a payload length and its signals."""

    frame_id: int
    name: str
    dlc: int
    signals: tuple[Signal, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0 <= self.dlc <= 8:
            raise ValueError("dlc must be 0..8")
        for s in self.signals:
            if s.start_bit + s.length > self.dlc * 8:
                raise ValueError(f"signal {s.name} does not fit in {self.dlc} bytes")

    def encode(self, values: dict[str, float]) -> bytes:
        unknown = set(values) - {s.name for s in self.signals}
        if unknown:
            raise KeyError(f"unknown signals: {sorted(unknown)}")
        word = 0
        for s in self.signals:
            raw = s.to_raw(values.get(s.name, s.offset))
            word |= (raw & ((1 << s.length) - 1)) << s.start_bit
        return word.to_bytes(self.dlc, "little")

    def decode(self, payload: bytes) -> dict[str, float]:
        if len(payload) != self.dlc:
            raise ValueError(f"{self.name}: expected {self.dlc} bytes, got {len(payload)}")
        word = int.from_bytes(payload, "little")
        out: dict[str, float] = {}
        for s in self.signals:
            raw = (word >> s.start_bit) & ((1 << s.length) - 1)
            if s.signed and raw >= 1 << (s.length - 1):
                raw -= 1 << s.length
            out[s.name] = s.to_physical(raw)
        return out


# ---- End-to-end protection: [crc8][counter][payload...] -------------------

def e2e_protect(payload: bytes, counter: int) -> bytes:
    counter &= 0x0F
    body = bytes([counter]) + payload
    return bytes([crc8(body)]) + body


def e2e_check(data: bytes, expected_counter: int | None = None) -> tuple[E2EStatus, bytes]:
    """Return (status, payload). Payload is empty unless status is OK."""
    if len(data) < 2:
        return E2EStatus.TOO_SHORT, b""
    if crc8(data[1:]) != data[0]:
        return E2EStatus.CRC_ERROR, b""
    if expected_counter is not None and data[1] != (expected_counter & 0x0F):
        return E2EStatus.COUNTER_ERROR, b""
    return E2EStatus.OK, data[2:]
