from . import package_analysis, apk_analysis, report_formatter
import utils.logging_utils.logging_engine as log
from config import app_config
from utils.display_utils import menu_utils, theme


def analyze_device(serial: str, artifact_limit: int | None = None) -> None:
    """Run static analysis against connected device packages."""

    log.info(f"Starting static analysis for device {serial}")

    if artifact_limit is None:
        artifact_limit = getattr(app_config, "ARTIFACT_LIMIT", 3)

    reports = package_analysis.analyze_packages(serial)
    report_formatter.print_reports(reports, serial, artifact_limit)


def analyze_apk_driver(apk_path: str):
    """Run static APK analysis via apk_analysis module."""
    metadata = apk_analysis.analyze_apk(apk_path)
    if not metadata:
        print(f"\n⚠️  No metadata extracted from {apk_path}\n")
        return

    print(f"\n🔍 APK Analysis for {apk_path}")
    print("----------------------------------")
    for k, v in metadata.items():
        print(f"{k:15}: {v}")
    log.info(f"APK analysis complete for {apk_path}")


def list_apk_hashes(serial: str) -> None:
    """Retrieve and print APK SHA-256 hashes for a device."""
    apk_map = package_analysis.get_installed_apk_paths(serial)
    if not apk_map:
        print(f"\n⚠️  No APKs found on {serial}\n")
        return

    hashes = package_analysis.compute_apk_hashes(serial, apk_map)
    if not hashes:
        print(f"\n⚠️  Failed to compute APK hashes for {serial}\n")
        return

    print(f"\n📦 APK hashes for {serial}")
    print("----------------------------------")
    for pkg, digest in hashes.items():
        print(f"{pkg:40} {digest}")
    log.info(f"Listed hashes for {len(hashes)} packages on {serial}")


def static_analysis_menu() -> None:
    """Interactive menu for static analysis tasks."""

    def _analyze_device():
        serial = input(theme.header("Enter device serial: ")).strip()
        if serial:
            analyze_device(serial)
        else:
            print("❌ No serial provided")

    def _analyze_apk():
        apk_path = input(theme.header("Enter path to APK: ")).strip()
        if apk_path:
            analyze_apk_driver(apk_path)
        else:
            print("❌ No APK path provided")

    def _list_hashes():
        serial = input(theme.header("Enter device serial: ")).strip()
        if serial:
            list_apk_hashes(serial)
        else:
            print("❌ No serial provided")

    options = {
        "1": ("Analyze device packages", _analyze_device),
        "2": ("Analyze single APK", _analyze_apk),
        "3": ("List device APK hashes", _list_hashes),
    }

    menu_utils.show_menu("Static Analysis", options, exit_label="Back")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    static_analysis_menu()
