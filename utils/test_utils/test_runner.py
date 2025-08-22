"""Helpers for running the project's test suite.

Providing a lightweight class for invoking ``pytest`` keeps the
responsibility of process management out of the menu layer and allows for
easier testing and future extensibility (e.g. collecting coverage or
passing through additional flags).
"""

from __future__ import annotations

from typing import List
import subprocess

import utils.logging_utils.logging_engine as log


class PytestRunner:
    """Thin wrapper around ``pytest`` execution."""

    def __init__(self, args: List[str] | None = None) -> None:
        self.args = args or ["pytest"]

    def run(self) -> subprocess.CompletedProcess:
        """Execute pytest with the configured arguments."""
        return subprocess.run(self.args, text=True)

    # The run_and_report function prints status to the console and logs the
    # outcome.  It returns ``True`` when all tests succeed.
    def run_and_report(self) -> bool:
        try:
            result = self.run()
        except Exception as exc:  # pragma: no cover - defensive
            print(f"❌ Failed to run tests: {exc}\n")
            log.error(f"Failed to run tests: {exc}")
            return False

        if result.returncode == 0:
            print("\n✅ All tests passed.\n")
            log.info("Test suite completed successfully")
            return True

        print("\n❌ Some tests failed. Review output above.\n")
        log.error("Test suite encountered failures")
        return False


__all__ = ["PytestRunner"]

