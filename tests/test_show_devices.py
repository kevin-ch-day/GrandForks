import sys
import re
from pathlib import Path
from typing import List

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from device.show_devices import display_detailed_devices, display_selection_devices
from utils.adb_utils.adb_devices import DeviceInfo

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def _sample_devices() -> List[DeviceInfo]:
    return [
        DeviceInfo(
            serial="ABC123",
            state="device",
            model="Pixel 4",
            type="Physical",
            details={"model": "Pixel 4", "vendor": "Google"},
        ),
        DeviceInfo(
            serial="XYZ789",
            state="offline",
            model="Nexus 5",
            type="Physical",
            details={"model": "Nexus 5", "vendor": "LG"},
        ),
    ]


def test_display_detailed_devices_json(monkeypatch):
    monkeypatch.setattr(
        "device.show_devices.get_connected_devices", lambda: _sample_devices()
    )
    monkeypatch.setattr(
        "device.device_formatter.adb_ip_lookup.get_ip_for_device", lambda s: "1.2.3.4"
    )

    result = display_detailed_devices(json_output=True)
    assert isinstance(result, list)
    assert result[0]["serial"] == "ABC123"
    assert result[0]["ip"] == "1.2.3.4"


def test_display_detailed_devices_print(monkeypatch, capfd):
    monkeypatch.setattr(
        "device.show_devices.get_connected_devices", lambda: _sample_devices()
    )
    monkeypatch.setattr(
        "device.device_formatter.adb_ip_lookup.get_ip_for_device", lambda s: "1.2.3.4"
    )

    rv = display_detailed_devices(json_output=False)
    out, _ = capfd.readouterr()
    clean = _strip_ansi(out)
    assert "Connected Devices" in clean
    assert "Vendor" in clean
    assert "DeviceInfo(" not in clean
    assert rv is None


def test_display_selection_devices_json(monkeypatch):
    monkeypatch.setattr(
        "device.show_devices.get_connected_devices", lambda: _sample_devices()
    )
    monkeypatch.setattr(
        "device.device_formatter.adb_ip_lookup.get_ip_for_device", lambda s: "1.2.3.4"
    )

    res = display_selection_devices(json_output=True)
    assert len(res) == 2
    assert res[1]["index"] == 2


def test_display_selection_devices_print(monkeypatch, capfd):
    monkeypatch.setattr(
        "device.show_devices.get_connected_devices", lambda: _sample_devices()
    )
    monkeypatch.setattr(
        "device.device_formatter.adb_ip_lookup.get_ip_for_device", lambda s: "1.2.3.4"
    )

    devices = display_selection_devices(json_output=False)
    out, _ = capfd.readouterr()
    clean = _strip_ansi(out)
    assert "Idx" in clean
    assert isinstance(devices[0], DeviceInfo)

    # Ensure header is rendered with separators
    lines = [l for l in clean.splitlines() if l.strip()]
    table_line = next(l for l in lines if "ABC123" in l)
    assert table_line.count("│") == 6
    fields = [f.strip() for f in table_line.split("│")]
    assert fields[1] == "Google"
    assert fields[2] == "Pixel 4"
    assert fields[3] == "ABC123"
    assert fields[4] == "[Physical]"
    assert fields[5] == "device"


def test_format_device_entry_ip_failure(monkeypatch):
    from device.device_formatter import format_device_entry

    monkeypatch.setattr(
        "device.device_formatter.adb_ip_lookup.get_ip_for_device",
        lambda s: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    dev = _sample_devices()[0]
    info = format_device_entry(1, dev)
    assert info["ip"] == "N/A"
