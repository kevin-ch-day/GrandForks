"""CSV helper utilities for project.

Provides a ``write_csv`` helper that enforces ``Package`` and ``APK_Path``
headers and ensures deterministic row ordering.  Additional helpers assist
with reading and validating APK lists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence, Mapping, Any, List, Dict
import csv

# Debugging helper prefix for all prints from this module
_DEBUG_PREFIX = "[csv_utils]"


_BASE_HEADERS = ["Package", "APK_Path"]


def _coerce_mapping(row: Mapping[str, Any] | Any, headers: Sequence[str]) -> Dict[str, Any]:
    """Return ``row`` as a mapping for ``headers``.

    ``row`` may already be a mapping or an object with attributes matching the
    headers.
    """

    if isinstance(row, Mapping):
        return {h: row.get(h) for h in headers}
    return {h: getattr(row, h, None) for h in headers}


def write_csv(path: str | Path, rows: Iterable[Mapping[str, Any] | Any], headers: Sequence[str]) -> None:
    """Write ``rows`` to ``path`` using UTF-8 encoding and ``\n`` line endings.

    The first two headers are forced to be ``Package`` and ``APK_Path``. Any
    additional ``headers`` are appended after these.  Rows are sorted
    case-insensitively by the ``Package`` column.
    """

    path = Path(path)
    extra_headers = [h for h in headers if h not in _BASE_HEADERS]
    fieldnames = _BASE_HEADERS + list(extra_headers)
    print(f"{_DEBUG_PREFIX} Preparing to write CSV to {path} with headers: {fieldnames}")

    coerced_rows: List[Dict[str, Any]] = []
    for row in rows:
        coerced = _coerce_mapping(row, fieldnames)
        coerced_rows.append(coerced)
    print(f"{_DEBUG_PREFIX} Coerced {len(coerced_rows)} row(s) for output")

    coerced_rows.sort(key=lambda r: (str(r.get("Package", "")).lower()))
    print(f"{_DEBUG_PREFIX} Sorted rows by 'Package' header")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in coerced_rows:
            writer.writerow(row)
    print(f"{_DEBUG_PREFIX} Wrote {len(coerced_rows)} row(s) to {path}")


def read_apk_list(path: str | Path) -> List[Dict[str, str]]:
    """Read an ``apk_list.csv`` style file into a list of dictionaries."""

    path = Path(path)
    print(f"{_DEBUG_PREFIX} Reading APK list from {path}")
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
    print(f"{_DEBUG_PREFIX} Loaded {len(rows)} row(s) from {path}")
    return rows


def validate_apk_list(path: str | Path) -> bool:
    """Return ``True`` if ``path`` exists and appears to be a valid APK list."""

    print(f"{_DEBUG_PREFIX} Validating APK list at {path}")
    try:
        path = Path(path)
        with path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print(f"{_DEBUG_PREFIX} Validation failed: missing headers")
                return False
            if reader.fieldnames[:2] != _BASE_HEADERS:
                print(f"{_DEBUG_PREFIX} Validation failed: incorrect base headers {reader.fieldnames[:2]}")
                return False
            for idx, row in enumerate(reader, start=1):
                if not row.get("Package") or not row.get("APK_Path"):
                    print(f"{_DEBUG_PREFIX} Validation failed: missing data at row {idx}")
                    return False
    except OSError as exc:
        print(f"{_DEBUG_PREFIX} Validation failed: {exc}")
        return False
    print(f"{_DEBUG_PREFIX} Validation succeeded for {path}")
    return True
