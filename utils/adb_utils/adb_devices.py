# utils/adb_utils/adb_devices.py
from dataclasses import dataclass, field
from typing import List, Dict

from utils.adb_utils import adb_runner
import utils.logging_utils.logging_engine as log


@dataclass
class DeviceInfo:
    """Structured information about a connected device."""

    serial: str
    state: str
    model: str
    type: str
    details: Dict[str, str] = field(default_factory=dict)


def get_connected_devices() -> List[DeviceInfo]:
    """Return structured information about connected devices."""
    result = adb_runner.run_adb_command(None, ["devices", "-l"])
    if not result.get("success", False):
        log.warning(f"ADB failed while listing devices :: {result.get('error')}")
        return []

    output = result.get("output")
    if not isinstance(output, str) or not output.strip():
        log.warning("No devices found")
        return []

    devices: List[DeviceInfo] = []
    for line in output.splitlines()[1:]:  # Skip header line
        if not line.strip():
            continue
        parts = line.split()
        serial = parts[0]
        state = parts[1] if len(parts) > 1 else "unknown"

        extras: Dict[str, str] = {}
        for part in parts[2:]:
            if ":" in part:
                key, val = part.split(":", 1)
                extras[key] = val
            else:
                extras[part] = "true"

        model = extras.get("model", "unknown")
        model_name = model.lower()
        is_virtual = serial.startswith("emulator-") or "sdk" in model_name or "emulator" in model_name
        dev_type = "Virtual" if is_virtual else "Physical"

        devices.append(
            DeviceInfo(
                serial=serial,
                state=state,
                model=model,
                type=dev_type,
                details=extras,
            )
        )

    log.info(f"Discovered {len(devices)} device(s)")
    return devices
