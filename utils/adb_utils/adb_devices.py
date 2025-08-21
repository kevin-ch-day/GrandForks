# utils/adb_utils/adb_devices.py
from utils.adb_utils import adb_runner
import utils.logging_utils.logging_engine as log
from typing import List, Dict


def get_connected_devices() -> List[Dict[str, str]]:
    """
    Returns a list of connected devices with their serial and state.
    Uses `adb devices -l` output.
    """
    output = adb_runner.run_adb_command("", ["devices", "-l"])
    if not output:
        return []

    devices = []
    for line in output.splitlines()[1:]:  # Skip header line
        if not line.strip():
            continue
        parts = line.split()
        serial = parts[0]
        state = parts[1] if len(parts) > 1 else "unknown"
        model = "unknown"
        for part in parts[2:]:
            if part.startswith("model:"):
                model = part.split(":", 1)[1]
        devices.append({"serial": serial, "state": state, "model": model})

    log.info(f"Discovered {len(devices)} device(s)")
    return devices
