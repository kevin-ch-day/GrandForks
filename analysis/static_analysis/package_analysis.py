"""Utilities for querying package information via adb."""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import logging

import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_runner import run_adb_command
from utils.display_utils.progress import Progress

# Prefer modular imports, but gracefully fallback if unavailable
try:
    from analysis.static_analysis.app_categories import get_category
    from analysis.static_analysis.permission_watchlist import SENSITIVE_PERMISSIONS
except ImportError:
    # Hardcoded mappings (fallback if static modules missing)
    KNOWN_APPS = {
        "com.facebook.katana": "Social Media",
        "com.instagram.android": "Social Media",
        "com.snapchat.android": "Social Media",
        "com.twitter.android": "Social Media",
        "com.tiktok.android": "Social Media",
        "com.whatsapp": "Messaging",
        "com.facebook.orca": "Messaging",
        "org.telegram.messenger": "Messaging",
        "com.bankofamerica.mobilebanking": "Financial",
        "com.chase.sig.android": "Financial",
    }

    SENSITIVE_PERMISSIONS = {
        "android.permission.RECORD_AUDIO",
        "android.permission.READ_SMS",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.SYSTEM_ALERT_WINDOW",
    }

    def get_category(pkg: str) -> str:
        """Fallback category resolver using KNOWN_APPS map."""
        return KNOWN_APPS.get(pkg, "Other")

try:
    from . import string_finder  # type: ignore
except Exception:  # pragma: no cover - fallback if module missing
    string_finder = None  # type: ignore


@dataclass
class PackageReport:
    """Summary information for a package discovered on a device."""

    name: str
    category: str
    permissions: List[str]
    dangerous_permissions: List[str]
    risk_score: int
    apk_hash: Optional[str] = None
    artifacts: Optional[List[str]] = None


def get_all_package_permissions(serial: str) -> Dict[str, List[str]]:
    """Return a mapping of package names to permission lists."""
    log.debug(f"Fetching full package dump for {serial}")
    result = run_adb_command(serial, ["shell", "dumpsys", "package"])

    if not result.get("success", False):
        log.warning(
            f"ADB failed while fetching package data for {serial} :: {result.get('error')}"
        )
        return {}

    output: Optional[str] = result.get("output")
    if not isinstance(output, str) or not output.strip():
        log.warning(f"No package data found for {serial}")
        return {}

    packages: Dict[str, List[str]] = {}
    current_pkg: Optional[str] = None
    count = 0
    progress_every = 25
    ticker = Progress("Parsed permissions", every=progress_every)
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("Package ["):
            end = line.find("]")
            if end != -1:
                current_pkg = line[len("Package [") : end]
                packages[current_pkg] = []
                count += 1
                ticker.update(count)
            continue

        if current_pkg and line.startswith(("uses-permission:", "permission:")):
            packages[current_pkg].append(line.split(":", 1)[-1].strip())

    ticker.total = count
    ticker.update(count)
    log.info(f"Parsed permissions for {count} packages in total")
    return packages


def get_installed_apk_paths(serial: str) -> Dict[str, str]:
    """Return a mapping of package names to APK paths on the device."""
    log.debug(f"Listing APK paths for {serial}")
    result = run_adb_command(
        serial, ["shell", "pm", "list", "packages", "-f", "-u", "--user", "0"]
    )

    if not result.get("success", False):
        log.warning(
            f"ADB failed while fetching APK paths for {serial} :: {result.get('error')}"
        )
        return {}

    output: Optional[str] = result.get("output")
    if not isinstance(output, str) or not output.strip():
        log.warning(f"No APK paths found for {serial}")
        return {}

    apk_paths: Dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("package:"):
            continue
        path_package = line[len("package:") :]
        path, _, pkg = path_package.partition("=")
        if pkg:
            apk_paths[pkg.strip()] = path.strip()

    log.info(f"Discovered APK paths for {len(apk_paths)} packages on {serial}")
    return apk_paths


def verify_package_apks(
    packages: Iterable[str],
    apk_paths: Dict[str, str],
    progress_every: int = 25,
) -> Tuple[Dict[str, str], List[str]]:
    """Validate that each package resolves to an APK path."""
    packages = list(packages)
    total = len(packages)
    log.info(f"Validating APK paths for {total} packages")

    valid: Dict[str, str] = {}
    missing: List[str] = []
    ticker = Progress("Validating APKs", total, progress_every)
    for idx, pkg in enumerate(packages, start=1):
        path = apk_paths.get(pkg)
        if path:
            valid[pkg] = path
            log.debug(f"APK for {pkg} located at {path}")
        else:
            missing.append(pkg)
            if _is_verbose_enabled():
                log.warning(f"No APK path found for {pkg}")
        ticker.update(idx)

    return valid, missing


def compute_apk_hashes(
    serial: str, apk_map: Dict[str, str], progress_every: int = 25
) -> Dict[str, str]:
    """Compute SHA-256 hashes for APKs in ``apk_map``."""
    total = len(apk_map)
    log.info(f"Computing hashes for {total} packages")

    hashes: Dict[str, str] = {}
    ticker = Progress("Hashing APKs", total, progress_every)
    for idx, (pkg, path) in enumerate(apk_map.items(), start=1):
        result = run_adb_command(serial, ["shell", "sha256sum", path])
        if result.get("success", False):
            output: Optional[str] = result.get("output")
            if isinstance(output, str) and output:
                hashes[pkg] = output.split()[0]
                log.debug(f"Hash for {pkg}: {hashes[pkg]}")
            else:
                log.warning(f"No hash output for {pkg}")
        else:
            log.warning(
                f"Failed to hash {pkg} :: {result.get('error', 'no error provided')}"
            )
        ticker.update(idx)

    return hashes


def analyze_packages(serial: str) -> List[PackageReport]:
    """Gather package, permission, and risk information for ``serial``."""
    perms_map = get_all_package_permissions(serial)
    apk_paths = get_installed_apk_paths(serial)
    verified_apks, missing = verify_package_apks(perms_map.keys(), apk_paths)

    if missing:
        log.info(f"Skipping {len(missing)} packages without APKs")

    hashes = compute_apk_hashes(serial, verified_apks)

    packages = list(verified_apks.keys())
    total = len(packages)
    reports: List[PackageReport] = []
    log.info(f"Analyzing {total} packages on {serial}")

    progress_every = 10
    ticker = Progress("Analyzing packages", total, progress_every)
    for idx, pkg in enumerate(packages, start=1):
        perms = perms_map.get(pkg, [])
        dangerous = [p for p in perms if p in SENSITIVE_PERMISSIONS]
        risk = len(dangerous)

        category = get_category(pkg)
        apk_hash = hashes.get(pkg)

        # Optional artifact analysis (if available)
        artifacts = None
        if string_finder:
            artifacts = string_finder.find_artifacts(serial, pkg)

        reports.append(
            PackageReport(
                name=pkg,
                category=category,
                permissions=perms,
                dangerous_permissions=dangerous,
                risk_score=risk,
                apk_hash=apk_hash,
                artifacts=artifacts,
            )
        )

        counters = string_finder.get_failure_counts() if string_finder else None
        ticker.update(idx, counters)

    flagged = sum(1 for r in reports if r.risk_score)
    log.info(
        f"Generated {len(reports)} package reports for {serial}; flagged {flagged} at-risk apps"
    )

    if string_finder:
        verbose = _is_verbose_enabled()
        string_finder.print_failure_summary(debug=verbose)

    return reports


def _is_verbose_enabled() -> bool:
    """Check if console logging is at DEBUG level."""

    logger = logging.getLogger()
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            return handler.level <= logging.DEBUG
    return False
