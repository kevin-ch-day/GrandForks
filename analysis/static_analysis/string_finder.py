"""Locate potential secrets inside an application's APK.

This module pulls the APK from a connected device and searches the
string table for URL patterns or possible API keys/secrets.  It is meant
as a lightweight helper for the static analysis pipeline and does not
attempt deep decompilation.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from typing import List, Mapping

import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_runner import run_adb_command
from .secret_scanner import scan as scan_secrets

# failure tracking
_failure_counts: Counter[str] = Counter()
_failure_details: List[str] = []


def get_failure_counts() -> Mapping[str, int]:
    """Expose current failure counters."""

    return dict(_failure_counts)


def _record_failure(pkg: str, reason: str, detail: str) -> None:
    """Track a failure ``reason`` for ``pkg`` with optional ``detail``."""

    _failure_counts[reason] += 1
    _failure_details.append(f"{pkg}: {detail}")

URL_RE = re.compile(r"https?://[^\s'\"]+")
SECRET_KEYWORDS = ["api_key", "apikey", "api-key", "secret", "token"]


def _pull_apk(serial: str, package: str) -> str | None:
    """Retrieve ``package`` APK from ``serial`` to a temporary path."""

    path_res = run_adb_command(
        serial, ["shell", "pm", "path", package], log_errors=False
    )
    if not path_res.get("success"):
        reason = path_res.get("error", "unknown error")
        _record_failure(package, "path", reason)
        log.debug(f"Failed to locate APK for {package} on {serial}: {reason}")
        return None

    output = path_res.get("output")
    if not isinstance(output, str):
        _record_failure(package, "path", str(output))
        log.debug(f"Unexpected pm path output for {package}: {output}")
        return None

    paths = [
        line.split(":", 1)[1].strip()
        for line in output.splitlines()
        if line.startswith("package:")
    ]
    if not paths:
        _record_failure(package, "path", output)
        log.debug(f"No valid pm path entries for {package}: {output}")
        return None

    remote_path = next((p for p in paths if p.endswith("base.apk")), paths[0])

    tmp_dir = tempfile.mkdtemp(prefix="apk_")
    local_path = os.path.join(tmp_dir, f"{package}.apk")
    pull_res = run_adb_command(
        serial, ["pull", remote_path, local_path], timeout=60, log_errors=False
    )
    if not pull_res.get("success"):
        error = pull_res.get("error", "unknown error").lower()
        if "denied" in error:
            reason = "denied"
        elif "not found" in error or "no such" in error:
            reason = "not found"
        else:
            reason = "other"
        _record_failure(package, reason, error)
        log.debug(f"Failed to pull APK for {package}: {error}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None
    return local_path


def _run_strings(path: str) -> str | None:
    """Run the ``strings`` utility on ``path`` and return its output."""

    if not shutil.which("strings"):
        log.warning("strings command not available")
        return None
    try:
        res = subprocess.run(["strings", "-a", path], capture_output=True, text=True, check=True)
        return res.stdout
    except (subprocess.CalledProcessError, OSError) as exc:
        log.warning(f"strings failed for {path}: {exc}")
        return None


def find_artifacts(serial: str, package: str) -> List[str]:
    """Pull ``package`` from ``serial`` and scan for potential secrets.

    Returns a list of suspicious string artifacts found within the APK.
    The list may include URLs or lines containing common secret keywords.
    """

    apk_path = _pull_apk(serial, package)
    if not apk_path:
        return []

    raw_strings = _run_strings(apk_path)
    # Clean up temporary APK regardless of success
    shutil.rmtree(os.path.dirname(apk_path), ignore_errors=True)
    if not raw_strings:
        return []

    artifacts: set[str] = set()
    artifacts.update(URL_RE.findall(raw_strings))

    for line in raw_strings.splitlines():
        lowered = line.lower()
        if any(k in lowered for k in SECRET_KEYWORDS):
            artifacts.add(line.strip())

    # Run regex-based secret scanner for more targeted tokens
    for matches in scan_secrets(raw_strings).values():
        artifacts.update(matches)

    return sorted(artifacts)


def print_failure_summary(verbose: bool = False) -> None:
    """Print and reset collected failure information."""

    if not _failure_counts:
        return

    print("\nFailure Summary")
    print("---------------")
    for reason, count in _failure_counts.items():
        print(f" - {reason}: {count}")
    if verbose and _failure_details:
        for detail in _failure_details:
            print(f"   {detail}")

    _failure_counts.clear()
    _failure_details.clear()
