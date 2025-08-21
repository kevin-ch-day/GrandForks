from __future__ import annotations

import hashlib
from typing import Dict, List

# Simple fingerprint database. Real deployments would likely load this from a
# remote feed or a configuration file.  The default entry is populated for the
# unit tests and represents the embedded DEX sample used there.
KNOWN_LIB_HASHES: Dict[str, str] = {
    # sha256: library name
    "ef17a9de095d3f5c0fce95ee78cfba455e43502c2cc3517ca0799b562f5ab2c3": "hello-lib",
}


def fingerprint_dex(path: str) -> List[str]:
    """Return names of known libraries detected in *path*.

    The detection is based on a SHA-256 hash of the DEX contents.  The hash is
    looked up in :data:`KNOWN_LIB_HASHES`.
    """

    with open(path, "rb") as fp:
        digest = hashlib.sha256(fp.read()).hexdigest()
    return [name for hash_, name in KNOWN_LIB_HASHES.items() if hash_ == digest]
