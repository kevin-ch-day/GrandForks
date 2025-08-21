"""Run feature extraction on reference apps for two device types and diff results."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict

# Ensure repository root is on the import path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import utils.logging_utils.logging_engine as log
from analysis.static_analysis import apk_analysis

REFERENCE_APPS = Path(__file__).with_name("reference_apps.json")
OUTPUT_DIR = Path("logs/benchmark")


def extract_features(apk_path: str) -> Dict[str, str]:
    """Run static feature extraction on an APK if available."""
    path = Path(apk_path)
    if not path.exists():
        log.error(f"APK not found: {apk_path}")
        return {}
    return apk_analysis.analyze_apk(str(path))


def diff_features(type_a: Dict[str, str], type_b: Dict[str, str]) -> Dict[str, Dict[str, str | None]]:
    """Compare two feature dictionaries and return mismatches."""
    diff: Dict[str, Dict[str, str | None]] = {}
    keys = set(type_a) | set(type_b)
    for key in keys:
        a_val = type_a.get(key)
        b_val = type_b.get(key)
        if a_val != b_val:
            diff[key] = {"type_a": a_val, "type_b": b_val}
    return diff


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not REFERENCE_APPS.exists():
        log.error(f"Reference app list missing: {REFERENCE_APPS}")
        return

    with REFERENCE_APPS.open() as fh:
        apps = json.load(fh)

    diff_lines = []
    for app in apps:
        name = app["name"]
        log.info(f"Processing {name}")
        a_features = extract_features(app["apk_path_a"])
        b_features = extract_features(app["apk_path_b"])

        (OUTPUT_DIR / f"{name}_type_a.json").write_text(json.dumps(a_features, indent=2))
        (OUTPUT_DIR / f"{name}_type_b.json").write_text(json.dumps(b_features, indent=2))

        diff = diff_features(a_features, b_features)
        if diff:
            diff_lines.append(f"{name}: {json.dumps(diff)}")

    diff_path = OUTPUT_DIR / "diff.log"
    diff_path.write_text("\n".join(diff_lines) if diff_lines else "No mismatches detected.\n")
    log.info(f"Benchmark complete. Diff report written to {diff_path}")


if __name__ == "__main__":
    main()
