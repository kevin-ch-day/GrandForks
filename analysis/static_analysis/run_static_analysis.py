from pathlib import Path

from . import (
    package_analysis,
    apk_analysis,
    report_formatter,
    string_finder,
    social_app_finder,
)
import utils.logging_utils.logging_engine as log
from config import app_config
from utils.display_utils import menu_utils, theme
from utils.adb_utils.adb_devices import get_connected_devices


def analyze_device(serial: str, artifact_limit: int | None = None) -> None:
    """Run static analysis against connected device packages."""

    print(f"\n📱 Starting static analysis for device {serial}")
    if artifact_limit is None:
        artifact_limit = getattr(app_config, "ARTIFACT_LIMIT", 3)

    print("Gathering packages from device...")
    reports = package_analysis.analyze_packages(serial)
    if not reports:
        print("⚠️  No packages found to analyze")
        return

    print(f"Analyzing {len(reports)} package(s)")
    report_formatter.print_reports(reports, serial, artifact_limit)
    print(f"✅ Static analysis complete for {serial}")
    log.info(f"Static analysis complete for {serial}")


def analyze_apk_driver(apk_path: str):
    """Run static APK analysis via apk_analysis module."""
    print(f"\n📦 Scanning APK at {apk_path}")
    metadata = apk_analysis.analyze_apk(apk_path)
    if not metadata:
        print(f"\n⚠️  No metadata extracted from {apk_path}\n")
        return

    print("Extracted metadata:")
    print("----------------------------------")
    for k, v in metadata.items():
        print(f"{k:15}: {v}")
    print("✅ APK analysis complete")
    log.info(f"APK analysis complete for {apk_path}")


def list_apk_hashes(serial: str) -> None:
    """Retrieve and print APK SHA-256 hashes for a device."""
    print(f"\n📁 Retrieving APK paths from {serial}")
    apk_map = package_analysis.get_installed_apk_paths(serial)
    if not apk_map:
        print(f"\n⚠️  No APKs found on {serial}\n")
        return

    print(f"Found {len(apk_map)} package(s); computing hashes...")
    hashes = package_analysis.compute_apk_hashes(serial, apk_map)
    if not hashes:
        print(f"\n⚠️  Failed to compute APK hashes for {serial}\n")
        return

    print(f"\n📦 APK hashes for {serial}")
    print("----------------------------------")
    for pkg, digest in hashes.items():
        print(f"{pkg:40} {digest}")
    print("✅ Hash listing complete")
    log.info(f"Listed hashes for {len(hashes)} packages on {serial}")


def scan_package_strings(serial: str, package: str) -> None:
    """Pull ``package`` from ``serial`` and scan for string artifacts."""

    print(f"\n🔍 Scanning {package} on {serial} for string artifacts")
    artifacts = string_finder.find_artifacts(serial, package)
    if not artifacts:
        print("No suspicious strings found")
    else:
        print(f"Found {len(artifacts)} potential artifact(s):")
        for art in artifacts:
            print(f" - {art}")
    string_finder.print_failure_summary()
    print("Scan complete")


def list_social_apps(serial: str) -> None:
    """Print any installed social applications detected on ``serial``."""

    print(f"\n👥 Searching for social apps on {serial}")
    apps = social_app_finder.find_social_apps(serial)
    if not apps:
        print("No social apps found")
        return

    for app in apps:
        print(f" - {app.package} ({app.app_name})")
    print("✅ Social app scan complete")


def _resolve_serial(provided: str | None) -> str | None:
    """Return a serial either from argument or automatic selection."""

    devices = get_connected_devices()
    if provided:
        if any(dev.serial == provided for dev in devices):
            print(f"Using provided serial: {provided}")
            return provided
        print(f"Provided serial {provided} not connected")
        return None

    if not devices:
        print("No connected devices found")
        return None

    if len(devices) > 1:
        print("Multiple devices detected. Specify one with --device.")
        return None

    serial = devices[0].serial
    print(f"Using connected device: {serial}")
    return serial


def validate_apk_path(apk_path: str) -> bool:
    """Return True if ``apk_path`` exists and points to an APK file."""

    if not apk_path:
        print("❌ No APK path provided")
        return False
    path = Path(apk_path)
    if not path.exists():
        print(f"❌ APK not found at {apk_path}")
        return False
    if path.suffix.lower() != ".apk":
        print(f"❌ {apk_path} is not an APK file")
        return False
    return True


def static_analysis_menu() -> None:
    """Interactive menu for static analysis tasks."""

    def _analyze_device():
        serial = _resolve_serial(None)
        if not serial:
            print("❌ No device selected")
            return
        limit_input = input(theme.header("Max reports to show (blank for default): ")).strip()
        limit = int(limit_input) if limit_input.isdigit() else None
        analyze_device(serial, artifact_limit=limit)

    def _analyze_apk():
        apk_path = input(theme.header("Enter path to APK: ")).strip()
        if not validate_apk_path(apk_path):
            return
        analyze_apk_driver(apk_path)

    def _scan_package():
        serial = _resolve_serial(None)
        if not serial:
            print("❌ No device selected")
            return
        pkg = input(theme.header("Enter package name: ")).strip()
        if not pkg:
            print("❌ No package name provided")
            return
        scan_package_strings(serial, pkg)

    def _find_social():
        serial = _resolve_serial(None)
        if not serial:
            print("❌ No device selected")
            return
        list_social_apps(serial)

    def _list_hashes():
        serial = _resolve_serial(None)
        if serial:
            list_apk_hashes(serial)
        else:
            print("❌ No device selected")

    options = {
        "1": ("Analyze device packages", _analyze_device),
        "2": ("Analyze single APK", _analyze_apk),
        "3": ("List device APK hashes", _list_hashes),
        "4": ("Scan package strings", _scan_package),
        "5": ("Find social apps", _find_social),
    }

    menu_utils.show_menu("Static Analysis", options, exit_label="Back")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    static_analysis_menu()
