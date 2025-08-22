"""Identify installed social media applications using discovery output.

This module relies on :mod:`discovery` to read the canonical APK inventory
CSV generated during device discovery. Packages are matched against a curated
list of social or messaging applications.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import discovery
from utils.adb_utils.adb_runner import run_adb_command

# Curated social app package -> label mapping lives in app_categories.
from .app_categories import SOCIAL_APP_LABELS as SOCIAL_APPS


@dataclass
class SocialApp:
    """Information collected about a detected social application."""

    package: str
    app_name: str
    apk_paths: List[str]
    label: Optional[str]
    metadata: Dict[str, str]


def find_social_apps(serial: str, apk_csv: str | Path = "apk_list.csv") -> List[SocialApp]:
    """Identify installed social apps on the device identified by ``serial``.

    Attempts to load package data from discovery CSV first, then falls back to
    ADB enumeration if necessary.
    """

    print(f"\n🔎 Searching for social apps on {serial}")
    packages, source = discovery.list_packages(serial, apk_csv)
    source_msg = f"{source} (CSV missing)" if source == "adb" else source
    print(f"  Loaded {len(packages)} package(s) from {source_msg}")

    found: List[SocialApp] = []
    unresolved: List[str] = []
    partitions = ["/data/app", "/system/app", "/vendor/app", "/product/app"]

    for pkg, apk_path in packages.items():
        if pkg not in SOCIAL_APPS:
            continue

        print(f"  Inspecting {pkg}")
        apk_paths: List[str] = [apk_path] if apk_path else []

        # If no path from discovery, query adb directly
        if not apk_paths:
            print(f"    Package {pkg} missing path; checking adb...")
            res = run_adb_command(serial, ["pm", "path", pkg], log_errors=False)
            if res.get("success") and res.get("output"):
                line = res["output"].splitlines()[0]
                if ":" in line:
                    adb_path = line.split(":", 1)[1]
                    apk_paths.append(adb_path)
                    print(f"    pm path found {adb_path}")

        # If still missing, search common partitions
        if not apk_paths:
            print("    pm path failed; searching common partitions...")
            for part in partitions:
                ls_res = run_adb_command(serial, ["ls", part], log_errors=False)
                if ls_res.get("success") and pkg in ls_res.get("output", ""):
                    found_path = f"{part}/{pkg}"
                    apk_paths.append(found_path)
                    print(f"    found in {found_path}")
                    break
                else:
                    print(f"    not found in {part}")

        if not apk_paths:
            unresolved.append(pkg)

        found.append(
            SocialApp(
                package=pkg,
                app_name=SOCIAL_APPS[pkg],
                apk_paths=apk_paths,
                label=None,
                metadata={},
            )
        )

    # Summary
    if found:
        print(f"Identified {len(found)} social app(s)")
    else:
        print("No known social apps detected")
    if unresolved:
        paths = ", ".join(partitions)
        print("Unresolved packages:")
        for pkg in unresolved:
            print(f"  {pkg}: searched {paths}")

    return found
