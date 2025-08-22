#!/usr/bin/env python3
"""CLI helper to run basic dynamic analysis on a device."""

from __future__ import annotations

import argparse
from pathlib import Path

from analysis.dynamic_analysis.run_dynamic_analysis import run_dynamic_analysis
from utils.adb_utils.adb_devices import get_connected_devices


def _resolve_serial(provided: str | None) -> str | None:
    """Return a serial either from argument or automatic selection."""

    if provided:
        print(f"Using provided serial: {provided}")
        return provided

    devices = get_connected_devices()
    if not devices:
        return None

    if len(devices) > 1:
        print("Multiple devices detected. Specify one with --device.")
        return None

    print(f"Using connected device: {devices[0].serial}")
    return devices[0].serial


def main(argv: list[str] | None = None) -> int:
    """Entry point for the dynamic analysis helper."""
    parser = argparse.ArgumentParser(description="Run basic dynamic analysis on a device")
    parser.add_argument(
        "--device",
        dest="serial",
        help="Target device serial; required if multiple devices are connected",
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
        print("No devices connected or selected")
        return 1

    if args.output_dir:
        print(f"Output directory set to: {args.output_dir.resolve()}")
    else:
        print("No output directory provided; using default 'dynamic_analysis'")

    print(f"Starting dynamic analysis on {serial}")
    run_dynamic_analysis(serial, output_dir=args.output_dir, duration=args.duration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
