import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.static_analysis import string_finder
from types import SimpleNamespace


def test_find_artifacts_reports_steps(monkeypatch, capsys):
    def fake_run_adb_command(serial, args, **kwargs):
        if args[:3] == ["shell", "pm", "path"]:
            return {"success": True, "output": "package:/data/app/pkg/base.apk"}
        if args[0] == "pull":
            return {"success": True, "output": ""}
        return {"success": False}

    monkeypatch.setattr(string_finder, "run_adb_command", fake_run_adb_command)
    monkeypatch.setattr(string_finder.shutil, "which", lambda cmd: True)
    monkeypatch.setattr(
        string_finder.subprocess,
        "run",
        lambda args, capture_output, text, check: SimpleNamespace(stdout="http://e.com"),
    )

    artifacts = string_finder.find_artifacts("SER", "pkg")
    out = capsys.readouterr().out
    assert "Locating APK for pkg" in out
    assert "Running strings on" in out
    assert artifacts
