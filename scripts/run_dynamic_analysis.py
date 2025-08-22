#!/usr/bin/env python3
"""CLI helper to run basic dynamic analysis on a device."""

from __future__ import annotations

import argparse
from pathlib import Path

from analysis.dynamic_analysis.run_dynamic_analysis import run_dynamic_analysis
from utils.adb_utils.adb_devices import get_connected_devices


def _resolve_serial(provided: str | None) -> str | None:
    """Return a serial either from argument or first connected device."""
    if provided:
        return provided
    devices = get_connected_devices()
    return devices[0].serial if devices else None


def main(argv: list[str] | None = None) -> int:
    """Entry point for the dynamic analysis helper."""
    parser = argparse.ArgumentParser(description="Run basic dynamic analysis on a device")
    parser.add_argument(
        "serial",
        nargs="?",
        help="Target device serial; defaults to first connected device",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where analysis artefacts are written",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=int,
        default=15,
        help="Maximum seconds to allow each adb command to run",
    )
    args = parser.parse_args(argv)

    serial = _resolve_serial(args.serial)
    if not serial:
        print("No devices connected")
        return 1

    run_dynamic_analysis(serial, output_dir=args.output_dir, duration=args.duration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
