# device/show_devices.py
"""Utilities for displaying connected devices.

This module delegates all formatting and printing to :mod:`device.device_formatter`
so that it only orchestrates device retrieval and error handling.
"""

from typing import Dict, List, Optional, Union

import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_devices import DeviceInfo, get_connected_devices

from .device_formatter import format_device_entry, pretty_print_device, print_device_table_header


def display_detailed_devices(
    json_output: bool = False,
) -> Optional[List[Dict[str, Union[str, int]]]]:
    """Display full details for each connected device.

    Args:
        json_output (bool): If ``True``, return a list of device dictionaries.
            Otherwise, pretty-print to stdout and return ``None``.
    """

    devices = get_connected_devices()
    if not devices:
        print("\n⚠️  No devices found.\n")
        log.warning("No devices detected via adb")
        return [] if json_output else None

    results: List[Dict[str, Union[str, int]]] = []

    if not json_output:
        print("\nConnected Devices")
        print("-------------------")

    for idx, d in enumerate(devices, start=1):
        dev_info = format_device_entry(idx, d)
        results.append(dev_info)

        if not json_output:
            pretty_print_device(dev_info)

        log.debug(f"Device {idx}: {dev_info}")

    if not json_output:
        print(f"\nTotal devices: {len(devices)}\n")
        return None

    return results


def display_selection_devices(
    json_output: bool = False,
) -> Union[List[Dict[str, Union[str, int]]], List[DeviceInfo]]:
    """Display a short list of devices for selection or return structured data.

    Args:
        json_output (bool): If ``True``, return a list of device dictionaries.
            Otherwise, pretty-print a concise list and return ``List[DeviceInfo]``.
    """

    devices = get_connected_devices()
    if not devices:
        print("\n⚠️  No devices found.\n")
        log.warning("No devices detected via adb")
        return []

    if not json_output:
        print("\nSelect a Device")
        print("-------------------")
        print_device_table_header()

    results: List[Dict[str, Union[str, int]]] = []

    for idx, d in enumerate(devices, start=1):
        dev_info = format_device_entry(idx, d)

        if json_output:
            results.append(dev_info)
        else:
            pretty_print_device(dev_info, detailed=False)

        log.debug(f"Device {idx}: {dev_info}")

    return results if json_output else devices

