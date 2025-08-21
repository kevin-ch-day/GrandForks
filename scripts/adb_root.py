#!/usr/bin/env python3
"""CLI helper to attempt adb root on a device."""

from __future__ import annotations

import argparse

from utils.adb_utils.adb_devices import get_connected_devices
from utils.adb_utils.adb_root import attempt_root


def _resolve_serial(provided: str | None) -> str | None:
    """Return a serial either from argument or first connected device."""
    if provided:
        return provided
    devices = get_connected_devices()
    return devices[0].serial if devices else None


def main(argv: list[str] | None = None) -> int:
    """Entry point for the adb root helper.

    Returns 0 if root access is granted, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description="Attempt to gain adb root on a device")
    parser.add_argument(
        "serial",
        nargs="?",
        help="Target device serial; defaults to first connected device",
    )
    args = parser.parse_args(argv)
    serial = _resolve_serial(args.serial)
    if not serial:
        print("No devices connected")
        return 1

    success = attempt_root(serial)
    msg = "Root access granted" if success else "Root access denied"
    print(f"{msg} for {serial}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
