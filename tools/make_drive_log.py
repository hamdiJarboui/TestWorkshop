"""Generate the recorded drive cycle used by Lab 9 (deterministic - safe to re-run).

Line format:  <time_s> <can_id_hex> <data_hex>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotest.bus import VirtualCANBus  # noqa: E402
from autotest.ecu import WheelSpeedECU  # noqa: E402

out = Path(sys.argv[1] if len(sys.argv) > 1 else "labs/lab09_regression_golden/data/drive_cycle.log")
bus = VirtualCANBus()
ecu = WheelSpeedECU(bus)
lines, t = [], 0.0
profile = [0, 10, 25, 40, 55, 70, 85, 100, 100, 100, 90, 70, 50, 30, 10, 0]
for i, speed in enumerate(profile):
    ecu.send_speed(speed)
    frame = bus.log[-1]
    data = frame.data.hex()
    if i == 5:                       # recorded corruption: one bit flipped on the wire
        data = f"{int(data[:2], 16) ^ 0x01:02x}{data[2:]}"
    lines.append(f"{t:.3f} {frame.arbitration_id:03x} {data}")
    t += 0.01
    if i == 9:                       # recorded gap: 250 ms bus silence
        t += 0.25
out.write_text("\n".join(lines) + "\n")
print(f"wrote {out} ({len(lines)} frames)")
