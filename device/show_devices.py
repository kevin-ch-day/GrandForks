# device/show_devices.py

from typing import Dict, Any, List, Optional, Union
import utils.logging_utils.logging_engine as log
from utils.adb_utils import adb_devices, adb_ip_lookup
from . import vendor_normalizer


def parse_device_line(line: str) -> Dict[str, Any]:
    """
    Parse a single `adb devices -l` line into structured data.

    Example input:
        emulator-5554 device product:sdk_gphone_x86 model:sdk_gphone_x86 ...
    """
    parts = line.split()
    if not parts:
        return {}

    serial: str = parts[0]
    state: str = parts[1] if len(parts) > 1 else "unknown"

    # Extra key=value pairs reported by adb
    extras: Dict[str, str] = {}
    for item in parts[2:]:
        if ":" in item:
            key, val = item.split(":", 1)
            extras[key] = val
        else:
            extras[item] = "true"

    # Distinguish emulators from physical devices
    model_name = extras.get("model", "").lower()
    is_virtual = serial.startswith("emulator-") or "sdk" in model_name or "emulator" in model_name
    device_type = "Virtual" if is_virtual else "Physical"

    return {
        "serial": serial,
        "state": state,
        "type": device_type,
        "details": extras,
    }


def get_connected_devices() -> List[Dict[str, Any]]:
    """
    Run `adb devices -l` and return structured device information.
    Returns a list of dicts with keys:
        serial, state, type, details (extras dict).
    """
    lines = adb_devices.run_adb_devices()

    if not lines:
        log.warning("No adb output received.")
        return []

    if lines[0].startswith("ERROR:"):
        error_msg = lines[0].replace("ERROR:", "").strip()
        log.error(f"adb error: {error_msg}")
        return [{"error": error_msg}]

    devices: List[Dict[str, Any]] = []
    for line in lines[1:]:  # skip adb header
        if line.strip():
            parsed = parse_device_line(line)
            if parsed:
                devices.append(parsed)

    return devices


def _resolve_ip(serial: str) -> Optional[str]:
    """Try to get the IP address of a device, safe-failing on error."""
    try:
        ip_result: Union[str, Dict[str, str], None] = adb_ip_lookup.get_ip_for_device(serial)
        if isinstance(ip_result, dict):
            return ip_result.get("ip")
        if isinstance(ip_result, str):
            return ip_result
    except Exception as e:
        log.warning(f"IP lookup failed for {serial}: {e}")
    return None


def display_detailed_devices() -> None:
    """Print full details for each connected device."""
    devices = get_connected_devices()

    if devices and "error" in devices[0]:
        error_msg = devices[0]["error"]
        print(f"\n❌ {error_msg}\n")
        return

    if not devices:
        print("\n⚠️  No devices found.\n")
        return

    print("\nConnected Devices")
    print("-------------------")

    for idx, d in enumerate(devices, start=1):
        details = d.get("details", {}) if isinstance(d.get("details"), dict) else {}
        serial = d.get("serial", "unknown")
        dev_type = d.get("type", "Unknown")
        state = d.get("state", "unknown")
        model = details.get("model", "unknown")
        vendor = vendor_normalizer.normalize_vendor(details)
        ip_addr = _resolve_ip(serial)

        print(f"[{idx}] {serial} ({dev_type} Device)")
        print(f"    Serial   : {serial}")
        print(f"    Vendor   : {vendor}")
        print(f"    Model    : {model}")
        print(f"    State    : {state}")
        if ip_addr:
            print(f"    IP Addr  : {ip_addr}")

        log.info(
            f"Device {idx}: serial={serial}, state={state}, "
            f"type={dev_type}, model={model}, vendor={vendor}"
        )

    print(f"\nTotal devices: {len(devices)}\n")


def display_selection_devices() -> List[Dict[str, Any]]:
    """Print a short numbered list of devices for user selection."""
    devices = get_connected_devices()

    if devices and "error" in devices[0]:
        error_msg = devices[0]["error"]
        print(f"\n❌ {error_msg}\n")
        return []

    if not devices:
        print("\n⚠️  No devices found.\n")
        return []

    print("\nSelect a Device")
    print("-------------------")
    for idx, d in enumerate(devices, start=1):
        details = d.get("details", {}) if isinstance(d.get("details"), dict) else {}
        vendor = vendor_normalizer.normalize_vendor(details)
        serial = d.get("serial", "unknown")
        dev_type = d.get("type", "Unknown")

        print(f"[{idx}] {vendor} {serial} ({dev_type} Device)")

    return devices
