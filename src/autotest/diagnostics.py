"""Diagnostic trouble codes (DTC) with debouncing and a UDS-lite request handler."""
from __future__ import annotations

from dataclasses import dataclass

NRC_SERVICE_NOT_SUPPORTED = 0x11
NRC_INCORRECT_LENGTH = 0x13
NRC_REQUEST_OUT_OF_RANGE = 0x31


@dataclass
class _DTC:
    fail_count: int = 0
    pass_count: int = 0
    active: bool = False
    stored: bool = False


class DiagnosticManager:
    """A DTC is confirmed after `fail_threshold` consecutive failures and
    stops being active after `heal_threshold` consecutive passes (it stays stored)."""

    VIN = b"WAUZZZ8K9BA123456"

    def __init__(self, fail_threshold: int = 3, heal_threshold: int = 5):
        if fail_threshold < 1 or heal_threshold < 1:
            raise ValueError("thresholds must be >= 1")
        self.fail_threshold = fail_threshold
        self.heal_threshold = heal_threshold
        self._dtcs: dict[str, _DTC] = {}

    @staticmethod
    def _validate(code: str) -> None:
        if len(code) != 5 or code[0] not in "PCBU" or not all(c in "0123456789ABCDEF" for c in code[1:]):
            raise ValueError(f"malformed DTC {code!r}")

    def report(self, code: str, failed: bool) -> None:
        self._validate(code)
        d = self._dtcs.setdefault(code, _DTC())
        if failed:
            d.fail_count, d.pass_count = d.fail_count + 1, 0
            if d.fail_count >= self.fail_threshold:
                d.active = d.stored = True
        else:
            d.pass_count, d.fail_count = d.pass_count + 1, 0
            if d.pass_count >= self.heal_threshold:
                d.active = False

    def active_codes(self) -> list[str]:
        return sorted(c for c, d in self._dtcs.items() if d.active)

    def stored_codes(self) -> list[str]:
        return sorted(c for c, d in self._dtcs.items() if d.stored)

    def clear_all(self) -> None:
        self._dtcs.clear()

    def export_report(self) -> str:
        lines = ["DTC REPORT", "=========="]
        for code in sorted(self._dtcs):
            d = self._dtcs[code]
            lines.append(f"{code} active={d.active} stored={d.stored}")
        if len(lines) == 2:
            lines.append("(no trouble codes)")
        return "\n".join(lines) + "\n"

    # ---- UDS-lite (ISO 14229 subset) -------------------------------------
    @staticmethod
    def _negative(service: int, nrc: int) -> bytes:
        return bytes([0x7F, service, nrc])

    def handle_request(self, request: bytes) -> bytes:
        if not request:
            return self._negative(0x00, NRC_INCORRECT_LENGTH)
        sid = request[0]
        if sid == 0x19:  # ReadDTCInformation, sub-function 0x02 = by status mask
            if len(request) != 3:
                return self._negative(sid, NRC_INCORRECT_LENGTH)
            if request[1] != 0x02:
                return self._negative(sid, NRC_REQUEST_OUT_OF_RANGE)
            body = b"".join(c.encode() + b";" for c in self.stored_codes())
            return bytes([0x59, 0x02]) + body
        if sid == 0x14:  # ClearDiagnosticInformation
            self.clear_all()
            return bytes([0x54])
        if sid == 0x22:  # ReadDataByIdentifier
            if len(request) != 3:
                return self._negative(sid, NRC_INCORRECT_LENGTH)
            if request[1:3] != b"\xF1\x90":
                return self._negative(sid, NRC_REQUEST_OUT_OF_RANGE)
            return bytes([0x62, 0xF1, 0x90]) + self.VIN
        return self._negative(sid, NRC_SERVICE_NOT_SUPPORTED)
