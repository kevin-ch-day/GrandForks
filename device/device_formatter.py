from typing import Dict, Union, Optional
from utils.adb_utils.adb_devices import DeviceInfo
from device import vendor_normalizer
from utils.adb_utils import adb_ip_lookup
import utils.logging_utils.logging_engine as log


def _resolve_ip(serial: str) -> Optional[str]:
    """Try to get the IP address of a device safely."""
    try:
        return adb_ip_lookup.get_ip_for_device(serial)
    except Exception as e:
        log.warning(f"IP lookup failed for {serial}: {e}")
        return None


def format_device_entry(idx: int, d: DeviceInfo) -> Dict[str, Union[str, int]]:
    """
    Format a device's details into a structured dictionary.

    Args:
        idx (int): Index number for the device.
        d (DeviceInfo): Device information object.

    Returns:
        Dict[str, Union[str, int]]: Structured device details with consistent keys.
    """
    details = d.details
    serial = d.serial or "N/A"
    dev_type = d.type or "Unknown"
    state = d.state or "Unknown"
    model = details.get("model", "Unknown")
    vendor = vendor_normalizer.normalize_vendor(details) or "Unknown"
    ip_addr = _resolve_ip(serial)

    return {
        "index": idx,
        "serial": serial,
        "type": dev_type,
        "vendor": vendor,
        "model": model,
        "state": state,
        "ip": ip_addr or "N/A",
    }


def pretty_print_device(device: Dict[str, Union[str, int]]) -> None:
    """
    Nicely print a formatted device entry.

    Args:
        device (Dict[str, Union[str, int]]): Device info dictionary.
    """
    print(f"[{device['index']}] {device['serial']} ({device['type']} Device)")
    print(f"    Serial   : {device['serial']}")
    print(f"    Vendor   : {device['vendor']}")
    print(f"    Model    : {device['model']}")
    print(f"    State    : {device['state']}")
    if device["ip"] and device["ip"] != "N/A":
        print(f"    IP Addr  : {device['ip']}")
