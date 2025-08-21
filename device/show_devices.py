# device/show_devices.py

from typing import List, Optional

import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_devices import DeviceInfo, get_connected_devices
from utils.adb_utils import adb_ip_lookup
from . import vendor_normalizer


def _resolve_ip(serial: str) -> Optional[str]:
    """Try to get the IP address of a device, safe-failing on error."""
    try:
        return adb_ip_lookup.get_ip_for_device(serial)
    except Exception as e:
        log.warning(f"IP lookup failed for {serial}: {e}")
        return None


def display_detailed_devices() -> None:
    """Print full details for each connected device."""
    devices = get_connected_devices()

    if not devices:
        print("\n⚠️  No devices found.\n")
        return

    print("\nConnected Devices")
    print("-------------------")

    for idx, d in enumerate(devices, start=1):
        details = d.details
        serial = d.serial
        dev_type = d.type
        state = d.state
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


def display_selection_devices() -> List[DeviceInfo]:
    """Print a short numbered list of devices for user selection."""
    devices = get_connected_devices()

    if not devices:
        print("\n⚠️  No devices found.\n")
        return []

    print("\nSelect a Device")
    print("-------------------")
    for idx, d in enumerate(devices, start=1):
        details = d.details
        vendor = vendor_normalizer.normalize_vendor(details)
        serial = d.serial
        dev_type = d.type

        print(f"[{idx}] {vendor} {serial} ({dev_type} Device)")

    return devices
