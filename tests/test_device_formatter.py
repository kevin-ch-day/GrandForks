import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from device import device_formatter


def strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def sample_device(dtype: str = "Physical"):
    return {
        "index": 1,
        "serial": "SER123",
        "type": dtype,
        "vendor": "Acme",
        "model": "Pixel",
        "state": "device",
        "ip": "1.2.3.4",
    }


def test_device_table_badges(capsys):
    device_formatter.print_device_table_header()
    device_formatter.pretty_print_device(sample_device("Physical"), detailed=False)
    out = capsys.readouterr().out
    plain = strip_ansi(out)
    assert "[Physical]" in plain
    assert "SER123" in plain
    assert "1.2.3.4" in plain
    # ensure muted color applied to IP
    assert "\x1b" in out
