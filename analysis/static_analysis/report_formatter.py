"""Formatting helpers for static analysis reports."""

from collections import Counter
from typing import Iterable, Optional, Mapping, Any

from utils.csv_utils import write_csv, read_apk_list, validate_apk_list

from .package_analysis import PackageReport
from .social_app_finder import SocialApp
import utils.logging_utils.logging_engine as log


def print_reports(
    reports: Iterable[PackageReport],
    serial: str,
    artifact_limit: Optional[int] = 3,
) -> None:
    """Render package reports and summary to the console."""

    reports = list(reports)
    if not reports:
        print(f"\n⚠️  No packages found on {serial}.")
        return

    print(f"\n📦 Installed Packages on {serial}")
    print("----------------------------------")
    for rep in reports:
        risk_marker = "!" if rep.risk_score else ""
        print(f" - {rep.name} [{rep.category}] {risk_marker}")
        if rep.apk_path:
            print(f"     📄 {rep.apk_path}")
        for perm in rep.dangerous_permissions[:5]:
            print(f"     ⚠ {perm}")
        if len(rep.dangerous_permissions) > 5:
            print("     ...")

        if rep.artifacts and artifact_limit != 0:
            limit = None if artifact_limit is None else artifact_limit
            shown = rep.artifacts if limit is None else rep.artifacts[:limit]
            for art in shown:
                print(f"     🔑 {art}")
            if limit is not None and len(rep.artifacts) > limit:
                remaining = len(rep.artifacts) - limit
                print(f"     (+{remaining} more)")

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
            if rep.artifacts and artifact_limit != 0:
                limit = None if artifact_limit is None else artifact_limit
                arts = rep.artifacts if limit is None else rep.artifacts[:limit]
                line = ", ".join(arts)
                if limit is not None and len(rep.artifacts) > limit:
                    remaining = len(rep.artifacts) - limit
                    line += f", (+{remaining} more)"
                print(f"     artifacts: {line}")

    print()
    log.info(f"Static analysis complete for {serial}")


def write_csv_report(
    reports: Iterable[PackageReport | Mapping[str, Any]], path: str
) -> None:
    """Write ``reports`` to ``path`` using :func:`utils.csv_utils.write_csv`.

    ``reports`` may contain :class:`PackageReport` instances or mapping-like
    objects with matching keys.
    """

    rows = []
    for rep in reports:
        if isinstance(rep, Mapping):
            pkg = rep.get("Package") or rep.get("package") or rep.get("name")
            apk = rep.get("APK_Path") or rep.get("apk_path")
            category = rep.get("Category") or rep.get("category")
            risk = rep.get("Risk_Score") or rep.get("risk_score")
        else:
            pkg = rep.name
            apk = rep.apk_path
            category = rep.category
            risk = rep.risk_score
        rows.append(
            {
                "Package": pkg,
                "APK_Path": apk or "",
                "Category": category,
                "Risk_Score": risk,
            }
        )

    print(
        f"[report_formatter] Writing {len(rows)} report row(s) to {path}"
    )
    write_csv(path, rows, headers=["Category", "Risk_Score"])

    # Debugging verification to ensure the file was written correctly
    if validate_apk_list(path):
        loaded = read_apk_list(path)
        print(
            f"[report_formatter] Verified CSV at {path} with {len(loaded)} row(s)"
        )
    else:
        print(f"[report_formatter] Warning: failed to validate written CSV at {path}")


def write_social_csv(apps: Iterable[SocialApp], path: str) -> None:
    """Write detected social apps to ``path`` as a CSV."""

    rows = []
    for app in apps:
        rows.append(
            {
                "Package": app.package,
                "APK_Path": ";".join(app.apk_paths),
                "App_Name": app.app_name,
                "Label": app.label or "",
            }
        )

    print(f"[report_formatter] Writing {len(rows)} social app row(s) to {path}")
    write_csv(path, rows, headers=["App_Name", "Label"])
