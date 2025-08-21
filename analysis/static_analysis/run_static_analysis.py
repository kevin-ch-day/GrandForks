from . import package_analysis, apk_analysis
import utils.logging_utils.logging_engine as log


def analyze_device(serial: str) -> None:
    """Run static analysis against connected device packages."""
    log.info(f"Starting static analysis for device {serial}")

    packages = package_analysis.list_installed_packages(serial)
    if not packages:
        print(f"\n⚠️  No packages found on {serial}.")
        return

    print(f"\n📦 Installed Packages on {serial}")
    print("----------------------------------")
    for pkg in packages[:20]:
        perms = package_analysis.get_package_permissions(serial, pkg)
        print(f" - {pkg}")
        for p in perms[:5]:
            print(f"     ↳ {p}")
        if len(perms) > 5:
            print("     ...")

    print(f"\nTotal packages: {len(packages)} (showing first 20)\n")
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
