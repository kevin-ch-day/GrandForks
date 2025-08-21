"""Formatting helpers for static analysis reports."""

from collections import Counter
from typing import Iterable, Optional

from .package_analysis import PackageReport
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
    for rep in reports[:20]:
        risk_marker = "!" if rep.risk_score else ""
        print(f" - {rep.name} [{rep.category}] {risk_marker}")
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
