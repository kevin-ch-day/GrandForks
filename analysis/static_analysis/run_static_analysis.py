from . import package_analysis, apk_analysis, report_formatter
import utils.logging_utils.logging_engine as log
from config import app_config


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
