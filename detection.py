"""Offline detection of social applications from an APK inventory CSV.

This module loads a CSV inventory (``apk_list.csv`` by default), looks for
packages installed in the "data" partition, and identifies social applications
either by an exact package match or via keyword tokens.  When matches are found,
a report is written to ``reports/social_apps_found.csv``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from config.social_detection import SOCIAL_APP_PACKAGES, KEYWORD_TOKENS
from utils.csv_utils import read_apk_list, write_csv


def detect(
    apk_csv: str | Path = "apk_list.csv",
    report_csv: str | Path = "reports/social_apps_found.csv",
) -> List[Dict[str, str]]:
    """Detect social apps listed in ``apk_csv``.

    Only rows where ``Install_Tier`` is ``"data"`` are considered.  Exact
    package matches are flagged with ``Detected`` set to ``"Y"`` and a
    ``Reason`` of ``"exact:<pkg>"``.  Rows whose package names contain any
    ``KEYWORD_TOKENS`` are marked with ``Detected`` set to ``"?"`` and
    ``Reason`` of ``"keyword:<token>"``.
    """

    apk_csv = Path(apk_csv)
    rows = read_apk_list(apk_csv)
    hits: List[Dict[str, str]] = []
    for row in rows:
        if row.get("Install_Tier") != "data":
            continue
        pkg = row.get("Package", "")
        if pkg in SOCIAL_APP_PACKAGES:
            row["Detected"] = "Y"
            row["Reason"] = f"exact:{pkg}"
            hits.append(row)
            continue
        lower_pkg = pkg.lower()
        token = next((t for t in KEYWORD_TOKENS if t in lower_pkg), None)
        if token:
            row["Detected"] = "?"
            row["Reason"] = f"keyword:{token}"
            hits.append(row)

    if not hits:
        return []

    extra_headers = [k for k in hits[0].keys() if k not in ("Package", "APK_Path")]
    write_csv(report_csv, hits, headers=extra_headers)
    return hits


if __name__ == "__main__":
    detect()
