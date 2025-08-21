"""Utilities for querying package information via adb."""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_runner import run_adb_command
from analysis.static_analysis.app_categories import get_category
from analysis.static_analysis.permission_watchlist import SENSITIVE_PERMISSIONS


@dataclass
class PackageReport:
    """Summary information for a package discovered on a device."""

    name: str
    category: str
    permissions: List[str]
    dangerous_permissions: List[str]
    risk_score: int
    apk_hash: Optional[str] = None


def get_all_package_permissions(serial: str) -> Dict[str, List[str]]:
    """Return a mapping of package names to permission lists.

    A single ``adb shell dumpsys package`` invocation is used to gather
    information for all packages rather than invoking ``dumpsys`` for each
    package individually. This dramatically reduces analysis time on devices
    with many installed applications.
    """

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
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("Package ["):
            end = line.find("]")
            if end != -1:
                current_pkg = line[len("Package [") : end]
                packages[current_pkg] = []
                count += 1
                if count % progress_every == 0:
                    log.info(f"Parsed permissions for {count} packages")
            continue

        if current_pkg and line.startswith(("uses-permission:", "permission:")):
            packages[current_pkg].append(line.split(":", 1)[-1].strip())

    log.info(f"Parsed permissions for {count} packages in total")
    return packages


def get_installed_apk_paths(serial: str) -> Dict[str, str]:
    """Return a mapping of package names to APK paths on the device."""

    log.debug(f"Listing APK paths for {serial}")
    result = run_adb_command(serial, ["shell", "pm", "list", "packages", "-f"])

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
    """Validate that each package resolves to an APK path.

    Returns a mapping of packages with valid APKs to their paths and a list of
    packages that could not be resolved.
    """

    packages = list(packages)
    total = len(packages)
    log.info(f"Validating APK paths for {total} packages")

    valid: Dict[str, str] = {}
    missing: List[str] = []
    for idx, pkg in enumerate(packages, start=1):
        path = apk_paths.get(pkg)
        if path:
            valid[pkg] = path
            log.debug(f"APK for {pkg} located at {path}")
        else:
            log.warning(f"No APK path found for {pkg}")
            missing.append(pkg)

        if idx % progress_every == 0 or idx == total:
            log.info(f"Validated {idx}/{total} packages")

    return valid, missing


def compute_apk_hashes(
    serial: str, apk_map: Dict[str, str], progress_every: int = 25
) -> Dict[str, str]:
    """Compute SHA-256 hashes for APKs in ``apk_map``."""

    total = len(apk_map)
    log.info(f"Computing hashes for {total} packages")

    hashes: Dict[str, str] = {}
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

        if idx % progress_every == 0 or idx == total:
            log.info(f"Hashed {idx}/{total} packages")

    return hashes


def analyze_packages(serial: str) -> List[PackageReport]:
    """Gather package, permission, and risk information for ``serial``.

    The returned list contains a :class:`PackageReport` entry for each
    package installed on the device. Each entry includes the package
    category, the full permission list, any dangerous permissions that
    were requested, and a simple risk score equal to the number of
    dangerous permissions.
    """

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
    for idx, pkg in enumerate(packages, start=1):
        perms = perms_map.get(pkg, [])
        dangerous = [p for p in perms if p in SENSITIVE_PERMISSIONS]
        risk = len(dangerous)
        category = get_category(pkg)
        apk_hash = hashes.get(pkg)
        log.debug(
            f"Package {pkg}: category={category}, risk={risk}, dangerous={dangerous}, hash={apk_hash}"
        )
        reports.append(
            PackageReport(
                name=pkg,
                category=category,
                permissions=perms,
                dangerous_permissions=dangerous,
                risk_score=risk,
                apk_hash=apk_hash,
            )
        )

        if idx % progress_every == 0 or idx == total:
            log.info(f"Processed {idx}/{total} packages")

    flagged = sum(1 for r in reports if r.risk_score)
    log.info(
        f"Generated {len(reports)} package reports for {serial}; flagged {flagged} at-risk apps"
    )

    return reports

