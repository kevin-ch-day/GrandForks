"""Pattern-based secret scanner for static analysis.

This module defines regular expressions for common API keys or tokens and
exposes a :func:`scan` helper that returns all matches grouped by type.
The goal is to complement the basic keyword search in :mod:`string_finder`
with more targeted heuristics so analysis can surface likely credentials
or secrets.
"""
from __future__ import annotations

import re
from typing import Dict, List, Mapping

# Registry of token patterns to search for in APK strings
PATTERNS: Mapping[str, re.Pattern[str]] = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "aws_secret_key": re.compile(
        r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}"
    ),
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "slack_token": re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,48}"),
    "github_token": re.compile(r"ghp_[0-9A-Za-z]{36}"),
    "jwt_token": re.compile(
        r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    ),
    "private_key": re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    # Generic `secret = value` style assignments with long values
    "generic_secret": re.compile(r"(?:secret|token|key)\s*[:=]\s*['\"]?[0-9A-Za-z_-]{8,}"),
}


def scan(text: str) -> Dict[str, List[str]]:
    """Return all pattern matches found within ``text`` while reporting progress."""

    print("Scanning text for secret patterns")
    results: Dict[str, List[str]] = {}
    for name, pattern in PATTERNS.items():
        hits = pattern.findall(text)
        print(f"  {name}: {len(hits)} hit(s)")
        if hits:
            results[name] = hits
    print("Secret scan complete")
    return results

__all__ = ["scan", "PATTERNS"]
