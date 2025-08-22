#!/usr/bin/env python3
"""Utility script for collecting APKs from a connected device.

The script reads a list of package names and, when the ``--pull`` flag is
provided, attempts to locate and download their base and split APKs.  Each
pulled APK is hashed (SHA-256) and recorded in ``reports/pulled_apks.csv``;
per-package hash digests are also saved alongside the APKs in
``apks/<PACKAGE>/<PACKAGE>.sha256.txt``.

Permission errors while pulling or hashing are handled gracefully and logged
so processing of other packages continues.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Iterable, List, Tuple

import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_runner import run_adb_command


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def list_apk_paths(serial: str | None, package: str) -> List[str]:
    """Return base and split APK paths for ``package``.

    Parameters
    ----------
    serial:
        Optional device serial.  If ``None``, ``run_adb_command`` will attempt
        auto-discovery when possible.
    package:
        Android package name to query.
    """
    result = run_adb_command(serial, ["shell", "pm", "path", package])
    if not result.get("success", False):
        log.warning(
            f"Failed to query APK paths for {package} :: {result.get('error', 'no error')}"
        )
        return []

    output = result.get("output", "")
    paths: List[str] = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            paths.append(line.split(":", 1)[1])
    return paths


def pull_apks(
    serial: str | None, package: str, paths: Iterable[str]
) -> List[Tuple[str, str, str]]:
    """Pull APKs for ``package`` and compute hashes.

    Returns a list of ``(package, local_path, sha256)`` tuples for successfully
    pulled files.
    """
    records: List[Tuple[str, str, str]] = []
    out_dir = Path("apks") / package
    out_dir.mkdir(parents=True, exist_ok=True)
    hash_path = out_dir / f"{package}.sha256.txt"

    for remote in paths:
        local_file = out_dir / Path(remote).name
        res = run_adb_command(serial, ["pull", remote, str(local_file)], timeout=60)
        if not res.get("success", False):
            err = res.get("error", "")
            out = res.get("output", "")
            msg = err or out
            if "Permission denied" in msg:
                log.warning(f"Permission denied pulling {remote} for {package}")
            else:
                log.warning(f"Failed to pull {remote} for {package} :: {msg}")
            continue

        try:
            digest = hashlib.sha256(local_file.read_bytes()).hexdigest()
        except PermissionError as exc:
            log.warning(f"Permission error hashing {local_file}: {exc}")
            continue

        try:
            with hash_path.open("a") as hf:
                hf.write(f"{digest}  {local_file.name}\n")
        except PermissionError as exc:
            log.warning(f"Permission error writing hash file for {package}: {exc}")

        records.append((package, str(local_file), digest))

    return records


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect APKs for packages")
    parser.add_argument(
        "serial", nargs="?", help="Target device serial; auto-detect if omitted"
    )
    parser.add_argument("packages", nargs="*", help="Package names to process")
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Pull APKs and compute SHA-256 hashes",
    )
    args = parser.parse_args(argv)

    if not args.packages:
        log.info("No packages specified; nothing to do")
        return 0

    all_records: List[Tuple[str, str, str]] = []
    for pkg in args.packages:
        paths = list_apk_paths(args.serial, pkg)
        if not paths:
            log.warning(f"No APK paths found for {pkg}")
            continue
        if args.pull:
            all_records.extend(pull_apks(args.serial, pkg, paths))
        else:
            for p in paths:
                print(f"{pkg}: {p}")

    if args.pull and all_records:
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        csv_path = reports_dir / "pulled_apks.csv"
        write_header = not csv_path.exists()
        try:
            with csv_path.open("a", newline="") as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(["package", "apk_path", "sha256"])
                writer.writerows(all_records)
        except PermissionError as exc:
            log.warning(f"Permission error writing {csv_path}: {exc}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
