from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class DexFeatureSchema:
    """Schema describing extracted DEX features.

    Attributes
    ----------
    class_count:
        Number of classes defined in the DEX file.
    method_count:
        Number of methods declared in the DEX file.
    uses_reflection:
        True when reflection APIs are referenced by the application.
    libraries:
        List of known third-party libraries detected via fingerprinting.
    """

    class_count: int
    method_count: int
    uses_reflection: bool
    libraries: List[str] = field(default_factory=list)
