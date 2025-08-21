"""Utilities for updating a single-line console progress ticker."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import Optional


class Progress:
    """Display incremental progress on a single console line.

    Parameters
    ----------
    label:
        Description for the progress line, e.g. ``"Pulling APKs"``.
    total:
        Optional total count.  If provided the output will render as
        ``"label: current/total"``.  When ``None`` only the current value is
        displayed.
    every:
        Only update the console every ``every`` calls to :meth:`update`.
    """

    def __init__(self, label: str, total: Optional[int] = None, every: int = 1):
        self.label = label
        self.total = total
        self.every = max(1, every)

    def update(self, current: int, counters: Optional[Mapping[str, int]] = None) -> None:
        """Render the ticker if the ``current`` count warrants an update."""

        if current % self.every != 0 and (self.total is None or current != self.total):
            return

        parts = [f"{self.label}: {current}"]
        if self.total is not None:
            parts[0] += f"/{self.total}"

        if counters:
            extra = ", ".join(f"{v} {k}" for k, v in counters.items())
            parts.append(f"({extra})")

        sys.stdout.write("\r" + " ".join(parts))
        sys.stdout.flush()

        if self.total is not None and current >= self.total:
            sys.stdout.write("\n")
            sys.stdout.flush()
