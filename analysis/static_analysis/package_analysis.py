"""Utilities for querying package information via adb."""

from dataclasses import dataclass
from typing import List, Optional, cast

import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_runner import run_adb_command

# Hardcoded mappings for known applications and their categories. These
# can be moved to an external config or database in the future.
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

# Watchlist of dangerous permissions. If an application requests any of
# these, it will be flagged in the report and contribute to its risk
# score.
SENSITIVE_PERMISSIONS = {
    "android.permission.RECORD_AUDIO",
    "android.permission.READ_SMS",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.SYSTEM_ALERT_WINDOW",
}


@dataclass
class PackageReport:
    """Summary information for a package discovered on a device."""

    name: str
    category: str
    permissions: List[str]
    dangerous_permissions: List[str]
    risk_score: int


def list_installed_packages(serial: str) -> List[str]:
    """List installed package names on the connected device."""

    log.info(f"Listing installed packages for {serial}")
    result = run_adb_command(serial, ["shell", "pm", "list", "packages"])

    if not result.get("success", False):
        log.warning(
            f"ADB failed while fetching package list for {serial} :: {result.get('error')}"
        )
        return []

    output = result.get("output")
    if not isinstance(output, str) or not output:
        log.warning(f"No packages found on {serial}")
        return []

    # Safe: output is a non-empty string at this point
    packages = [line.replace("package:", "").strip() for line in output.splitlines()]
    log.info(f"Found {len(packages)} packages on {serial}")
    return packages


def _parse_permissions(dumpsys_output: str) -> List[str]:
    """Parse permissions from ``dumpsys package`` output."""

    perms: List[str] = []
    for line in dumpsys_output.splitlines():
        line = line.strip()
        if line.startswith(("uses-permission:", "permission:")):
            perms.append(line.split(":")[-1].strip())
    return perms


def get_package_permissions(serial: str, package: str) -> List[str]:
    """Return a list of declared permissions for ``package`` on the device."""

    log.info(f"Fetching permissions for {package} on {serial}")
    result = run_adb_command(serial, ["shell", "dumpsys", "package", package])

    if not result.get("success", False):
        log.warning(
            f"ADB failed while fetching permissions for {package} on {serial} :: {result.get('error')}"
        )
        return []

    output: Optional[str] = result.get("output")
    if not isinstance(output, str) or not output.strip():
        log.warning(f"No permission data found for {package} on {serial}")
        return []

    return _parse_permissions(cast(str, output))


def analyze_packages(serial: str) -> List[PackageReport]:
    """Gather package, permission, and risk information for ``serial``.

    The returned list contains a :class:`PackageReport` entry for each
    package installed on the device. Each entry includes the package
    category, the full permission list, any dangerous permissions that
    were requested, and a simple risk score equal to the number of
    dangerous permissions.
    """

    packages = list_installed_packages(serial)
    reports: List[PackageReport] = []

    for pkg in packages:
        perms = get_package_permissions(serial, pkg)
        dangerous = [p for p in perms if p in SENSITIVE_PERMISSIONS]
        risk = len(dangerous)
        category = KNOWN_APPS.get(pkg, "Other")
        log.debug(
            f"Package {pkg}: category={category}, risk={risk}, dangerous={dangerous}"
        )
        reports.append(
            PackageReport(
                name=pkg,
                category=category,
                permissions=perms,
                dangerous_permissions=dangerous,
                risk_score=risk,
            )
        )

    flagged = sum(1 for r in reports if r.risk_score)
    log.info(
        f"Generated {len(reports)} package reports for {serial}; flagged {flagged} at-risk apps"
    )

    return reports

