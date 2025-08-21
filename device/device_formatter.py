"""Helpers for formatting and printing device information."""

from typing import Dict, Union

from utils.adb_utils.adb_devices import DeviceInfo
from device import vendor_normalizer
from utils.adb_utils import adb_ip_lookup
import utils.logging_utils.logging_engine as log

# ---- Display constants ----------------------------------------------------
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

IDX_W, VENDOR_W, MODEL_W, SERIAL_W, TYPE_W, STATE_W, IP_W = 4, 12, 15, 16, 9, 10, 15
_COLS = [IDX_W, VENDOR_W, MODEL_W, SERIAL_W, TYPE_W, STATE_W, IP_W]
_TABLE_WIDTH = sum(_COLS) + 3 * (len(_COLS) - 1)


def _resolve_ip(serial: str) -> str:
    """Try to get the IP address of a device, return 'N/A' on error."""
    try:
        return adb_ip_lookup.get_ip_for_device(serial) or "N/A"
    except Exception as e:
        log.warning(f"IP lookup failed for {serial}: {e}")
        return "N/A"


def _colorize_state(state: str) -> str:
    """Return an ANSI-colored representation of the device state."""
    s = state.lower()
    if s == "device":
        return f"{GREEN}{state}{RESET}"
    if s == "offline":
        return f"{RED}{state}{RESET}"
    return f"{YELLOW}{state}{RESET}"


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
        "ip": ip_addr,
    }


def print_device_table_header() -> None:
    """Print a table header for the short device list."""
    header = (
        f"{BOLD}{CYAN}{'Idx':<{IDX_W}} │ {'Vendor':<{VENDOR_W}} │ "
        f"{'Model':<{MODEL_W}} │ {'Serial':<{SERIAL_W}} │ "
        f"{'Type':<{TYPE_W}} │ {'State':<{STATE_W}} │ {'IP':<{IP_W}}{RESET}"
    )
    print(header)
    print("─" * _TABLE_WIDTH)


def pretty_print_device(device: Dict[str, Union[str, int]], detailed: bool = True) -> None:
    """Nicely print a formatted device entry."""

    state_col = _colorize_state(str(device["state"]))

    if detailed:
        print(f"{BOLD}[{device['index']}] {device['serial']} ({device['type']} Device){RESET}")
        print(f"    Vendor   : {device['vendor']}")
        print(f"    Model    : {device['model']}")
        print(f"    State    : {state_col}")
        print(f"    IP Addr  : {device['ip']}")
        print()
    else:
        index_str = f"[{device['index']}]"
        # The colored state text needs padding calculated from the plain value
        state_plain = str(device["state"])
        padding = " " * (STATE_W - len(state_plain))
        state_field = f"{state_col}{padding}"
        line = (
            f"{index_str:<{IDX_W}} │ "
            f"{device['vendor']:<{VENDOR_W}} │ {device['model']:<{MODEL_W}} │ "
            f"{device['serial']:<{SERIAL_W}} │ {device['type']:<{TYPE_W}} │ "
            f"{state_field} │ {device['ip']:<{IP_W}}"
        )
        print(line)
