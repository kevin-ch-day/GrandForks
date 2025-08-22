import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.dynamic_analysis.run_dynamic_analysis import run_dynamic_analysis


def test_run_dynamic_analysis_collects_logs(tmp_path, capsys, monkeypatch):
    calls = []

    def fake_run_adb_command(serial, args, timeout=15, capture_stderr=False, log_errors=True):
        calls.append((serial, args, timeout))
        if args == ["logcat", "-d"]:
            return {"success": True, "output": "log output", "error": ""}
        if args == ["shell", "dumpsys", "activity", "activities"]:
            return {"success": True, "output": "activity output", "error": ""}
        return {"success": False, "output": "", "error": "unexpected"}

    monkeypatch.setattr(
        "analysis.dynamic_analysis.run_dynamic_analysis.run_adb_command",
        fake_run_adb_command,
    )

    paths = run_dynamic_analysis("serial123", output_dir=tmp_path, duration=5)

    out_lines = capsys.readouterr().out.strip().splitlines()
    assert "Dynamic analysis complete for serial123" in out_lines[0]
    assert (tmp_path / "logcat.txt").read_text() == "log output"
    assert (tmp_path / "activity.txt").read_text() == "activity output"
    assert paths["logcat"] == tmp_path / "logcat.txt"
    assert paths["activity"] == tmp_path / "activity.txt"

    # Ensure duration parameter is forwarded to adb commands
    assert calls[0][2] == 5
    assert calls[1][2] == 5

