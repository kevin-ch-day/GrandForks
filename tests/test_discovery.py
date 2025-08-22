import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import discovery


def test_list_packages_fallback_to_adb(monkeypatch):
    def fake_read_apk_list(_):
        raise OSError

    def fake_run_adb_command(serial, args, **kwargs):
        return {
            "success": True,
            "output": "/data/app/com.example/base.apk=com.example\n",
            "error": "",
        }

    monkeypatch.setattr(discovery, "read_apk_list", fake_read_apk_list)
    monkeypatch.setattr(discovery.adb_runner, "run_adb_command", fake_run_adb_command)

    packages, source = discovery.list_packages("SER", "missing.csv")
    assert source == "adb"
    assert packages == {"com.example": "/data/app/com.example/base.apk"}
