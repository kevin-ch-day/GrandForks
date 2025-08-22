"""Identify installed social media applications via ADB.

This module provides helpers to list third-party packages on a connected
Android device and flag any packages that match a curated list of social
media or messaging applications. For each match, basic metadata can be
retrieved via ``dumpsys package``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import utils.logging_utils.logging_engine as log
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


def _parse_package_listing(output: str) -> Dict[str, str]:
    """Parse ``pm list packages -f`` output into ``{package: path}`` mapping."""
    packages: Dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("package:"):
            continue
        path_pkg = line[len("package:") :]
        path, _, pkg = path_pkg.partition("=")
        if pkg:
            packages[pkg.strip()] = path.strip()
    return packages


def get_third_party_packages(serial: str) -> Dict[str, str]:
    """Return mapping of installed third-party packages to their APK path."""
    result = run_adb_command(serial, ["shell", "pm", "list", "packages", "-f", "-3"])
    if not result.get("success", False):
        log.warning(
            f"ADB failed while listing packages for {serial} :: {result.get('error', '')}"
        )
        return {}

    output = result.get("output") or ""
    return _parse_package_listing(str(output))


def get_apk_paths(serial: str, package: str) -> List[str]:
    """Return all APK paths for ``package`` using ``pm path``."""
    result = run_adb_command(serial, ["shell", "pm", "path", package])
    if not result.get("success", False):
        log.debug(f"Failed to resolve APK path for {package}: {result.get('error', '')}")
        return []

    paths: List[str] = []
    output = result.get("output") or ""
    for line in str(output).splitlines():
        line = line.strip()
        if line.startswith("package:"):
            paths.append(line[len("package:") :])
    return paths


def get_app_info(serial: str, package: str) -> tuple[Optional[str], Dict[str, str]]:
    """Return application label and basic metadata for ``package``."""
    result = run_adb_command(serial, ["shell", "dumpsys", "package", package])
    if not result.get("success", False):
        log.debug(f"Failed to dumpsys {package}: {result.get('error', '')}")
        return None, {}

    label: Optional[str] = None
    meta: Dict[str, str] = {}
    output = str(result.get("output") or "")
    for raw in output.splitlines():
        line = raw.strip()
        if line.startswith("application-label:"):
            label = line.split(":", 1)[1].strip()
        elif any(
            line.startswith(prefix)
            for prefix in (
                "versionName=",
                "versionCode=",
                "installerPackageName=",
                "uid=",
            )
        ):
            key, _, value = line.partition("=")
            meta[key] = value.strip()
    return label, meta


def find_social_apps(serial: str) -> List[SocialApp]:
    """Identify installed social apps on the device identified by ``serial``."""
    packages = get_third_party_packages(serial)
    found: List[SocialApp] = []
    for pkg in packages:
        if pkg not in SOCIAL_APPS:
            continue
        apk_paths = get_apk_paths(serial, pkg)
        label, meta = get_app_info(serial, pkg)
        found.append(
            SocialApp(
                package=pkg,
                app_name=SOCIAL_APPS[pkg],
                apk_paths=apk_paths,
                label=label,
                metadata=meta,
            )
        )
    return found
