# device/show_devices.py

from typing import List, Optional, Dict
import utils.logging_utils.logging_engine as log
from utils.adb_utils import adb_devices, adb_utils, adb_ip_lookup
from . import vendor_normalizer, device_formatter


def _resolve_ip(serial: str) -> str:
    """Try to get the IP address of a device, return 'N/A' on error."""
    try:
        return adb_ip_lookup.get_ip_for_device(serial) or "N/A"
    except Exception as e:
        log.warning(f"IP lookup failed for {serial}: {e}")
        return "N/A"


def display_detailed_devices(json_output: bool = False) -> Optional[List[Dict[str, str]]]:
    """Print full details for each connected device, or return as list of dicts."""
    devices = adb_utils.get_connected_devices()

    if not devices:
        print("\n⚠️  No devices found.\n")
        log.warning("No devices detected via adb")
        return [] if json_output else None

    results = []

    print("\nConnected Devices")
    print("-------------------")

    for idx, d in enumerate(devices, start=1):
        dev_info = _format_device_entry(idx, d)
        results.append(dev_info)

        if not json_output:  # human-friendly output
            print(f"[{dev_info['index']}] {dev_info['serial']} ({dev_info['type']} Device)")
            print(f"    Vendor   : {dev_info['vendor']}")
            print(f"    Model    : {dev_info['model']}")
            print(f"    State    : {dev_info['state']}")
            print(f"    IP Addr  : {dev_info['ip']}")
            print()

        log.info(
            f"Device {idx}: serial={dev_info['serial']}, state={dev_info['state']}, "
            f"type={dev_info['type']}, model={dev_info['model']}, vendor={dev_info['vendor']}, ip={dev_info['ip']}"
        )

    if not json_output:
        print(f"\nTotal devices: {len(devices)}\n")

    return results if json_output else None


def display_selection_devices(json_output: bool = False) -> List[DeviceInfo]:
    """Print a short numbered list of devices for user selection, or return JSON."""
    devices = get_connected_devices()

    if not devices:
        print("\n⚠️  No devices found.\n")
        log.warning("No devices detected via adb")
        return []

    if not json_output:
        print("\nSelect a Device")
        print("-------------------")

    results = []

    for idx, d in enumerate(devices, start=1):
        details = d.details
        vendor = vendor_normalizer.normalize_vendor(details) or "Unknown"
        serial = d.serial or "N/A"
        dev_type = d.type or "Unknown"

        if not json_output:
            print(f"[{idx}] {vendor} {serial} ({dev_type} Device)")

        results.append({
            "index": idx,
            "vendor": vendor,
            "serial": serial,
            "type": dev_type,
        })

    return results if json_output else devices
