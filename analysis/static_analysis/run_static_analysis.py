from collections import Counter

from . import package_analysis, apk_analysis
import utils.logging_utils.logging_engine as log


def analyze_device(serial: str) -> None:
    """Run static analysis against connected device packages."""

    log.info(f"Starting static analysis for device {serial}")

    reports = package_analysis.analyze_packages(serial)
    if not reports:
        print(f"\n⚠️  No packages found on {serial}.")
        return

    print(f"\n📦 Installed Packages on {serial}")
    print("----------------------------------")
    for rep in reports[:20]:
        risk_marker = "!" if rep.risk_score else ""
        print(f" - {rep.name} [{rep.category}] {risk_marker}")
        for perm in rep.dangerous_permissions[:5]:
            print(f"     ⚠ {perm}")
        if len(rep.dangerous_permissions) > 5:
            print("     ...")

    flagged = [r for r in reports if r.risk_score]
    category_counts = Counter(r.category for r in reports)

    print("\nSummary")
    print("-------")
    print(f"Total packages: {len(reports)}")
    print(f"Flagged apps : {len(flagged)}")
    for cat, count in category_counts.items():
        print(f" - {cat}: {count}")

    if flagged:
        print("\nFlagged applications:")
        for rep in flagged:
            perms = ", ".join(rep.dangerous_permissions)
            print(
                f" - {rep.name} [{rep.category}] risk={rep.risk_score} :: {perms}"
            )

    print()
    log.info(f"Static analysis complete for {serial}")


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
