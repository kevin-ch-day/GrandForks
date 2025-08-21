from __future__ import annotations

import base64

import pytest

from analysis.dex_features import parse_dex_features
from analysis.dex_features.fingerprinting import fingerprint_dex


# Base64 representation of a minimal DEX file used for tests.  The data was
# previously stored as ``tests/hello.dex`` but is now embedded here to avoid
# shipping binary artifacts in the repository.
HELLO_DEX_B64 = (
    "ZGV4CjAzNQA6XhkMZcwIftV2X0TCAHQjQQ4EO8A1Q1PsAgAAcAAAAHhWNBIAAAAAAAAAAEwCAA"
    "AOAAAAcAAAAAcAAACoAAAAAwAAAMQAAAABAAAA6AAAAAQAAADwAAAAAQAAABABAAC8AQAAMAEAA"
    "HYBAAB+AQAAjQEAAJ4BAACsAQAAwwEAANcBAADrAQAA/wEAAAICAAAGAgAAGwIAACECAAAmAgAA"
    "AwAAAAQAAAAFAAAABgAAAAcAAAAIAAAACgAAAAgAAAAFAAAAAAAAAAkAAAAFAAAAaAEAAAkAAAAF"
    "AAAAcAEAAAQAAQAMAAAAAAAAAAAAAAAAAAIACwAAAAEAAQANAAAAAgAAAAAAAAAAAAAAAAAAAAIA"
    "AAAAAAAAAgAAAAAAAAA7AgAAAAAAAAEAAQABAAAALwIAAAQAAABwEAMAAAAOAAMAAQACAAAANAIA"
    "AAgAAABiAAAAGgEBAG4gAgAQAA4AAQAAAAMAAAABAAAABgAGPGluaXQ+AA1IZWxsbywgV29ybGQh"
    "AA9IZWxsb1dvcmxkLmphdmEADExIZWxsb1dvcmxkOwAVTGphdmEvaW8vUHJpbnRTdHJlYW07ABJM"
    "amF2YS9sYW5nL09iamVjdDsAEkxqYXZhL2xhbmcvU3RyaW5nOwASTGphdmEvbGFuZy9TeXN0ZW07"
    "AAFWAAJWTAATW0xqYXZhL2xhbmcvU3RyaW5nOwAEbWFpbgADb3V0AAdwcmludGxuAAEABw4AAwEA"
    "Bw54AAAAAgAAgIAEsAIBCcgCAAAADQAAAAAAAAABAAAAAAAAAAEAAAAOAAAAcAAAAAIAAAAHAAAA"
    "qAAAAAMAAAADAAAAxAAAAAQAAAABAAAA6AAAAAUAAAAEAAAA8AAAAAYAAAABAAAAEAEAAAEgAAAC"
    "AAAAMAEAAAEQAAACAAAAaAEAAAIgAAAOAAAAdgEAAAMgAAACAAAALwIAAAAgAAABAAAAOwIAAAAQ"
    "AAABAAAATAIAAA=="
)


@pytest.fixture()
def hello_dex(tmp_path):
    """Write the embedded DEX to a temporary path and return the filename."""

    data = base64.b64decode(HELLO_DEX_B64)
    path = tmp_path / "hello.dex"
    path.write_bytes(data)
    return str(path)


def test_parse_dex_features_counts_and_reflection(hello_dex):
    features = parse_dex_features(hello_dex)
    assert features.class_count == 1
    assert features.method_count == 4
    assert features.uses_reflection is False
    assert features.libraries == ["hello-lib"]


def test_fingerprint_dex_matches_known_hash(hello_dex):
    libs = fingerprint_dex(hello_dex)
    assert libs == ["hello-lib"]
