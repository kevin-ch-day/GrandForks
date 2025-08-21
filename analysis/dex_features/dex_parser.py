from __future__ import annotations

from androguard.core.dex import DEX

from .fingerprinting import fingerprint_dex
from .schema import DexFeatureSchema


REFLECTION_MARKERS = (
    "java/lang/reflect",  # Generic reflection package
    "Class.forName",      # Dynamic class loading
    "getMethod",          # Method lookup
    "invoke",             # java.lang.reflect.Method#invoke
)


def parse_dex_features(path: str) -> DexFeatureSchema:
    """Parse *path* and return :class:`DexFeatureSchema`.

    Parameters
    ----------
    path:
        Path to a ``classes.dex`` file.
    """

    with open(path, "rb") as fp:
        dex = DEX(fp.read())

    classes = dex.get_classes()
    methods = dex.get_methods()
    strings = dex.get_strings()

    class_count = len(classes)
    method_count = len(methods)

    string_hits = any(any(marker in s for marker in REFLECTION_MARKERS) for s in strings)
    method_hits = any(
        any(marker in (m.get_name() or "") for marker in REFLECTION_MARKERS) for m in methods
    )
    uses_reflection = string_hits or method_hits

    libraries = fingerprint_dex(path)
    return DexFeatureSchema(
        class_count=class_count,
        method_count=method_count,
        uses_reflection=uses_reflection,
        libraries=libraries,
    )
