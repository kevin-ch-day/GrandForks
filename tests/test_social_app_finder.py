import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.static_analysis import social_app_finder


def test_find_social_apps_reports(monkeypatch, capsys):
    def fake_run_adb_command(serial, args, **kwargs):
        if args[:5] == ["shell", "pm", "list", "packages", "-f"]:
            return {"success": True, "output": "package:/data/app/com.snapchat.android/base.apk=com.snapchat.android"}
        if args[:3] == ["shell", "pm", "path"]:
            return {"success": True, "output": "package:/data/app/com.snapchat.android/base.apk"}
        if args[:3] == ["shell", "dumpsys", "package"]:
            return {"success": True, "output": "application-label:Snapchat"}
        return {"success": False}

    monkeypatch.setattr(social_app_finder, "run_adb_command", fake_run_adb_command)
    apps = social_app_finder.find_social_apps("SER")
    out = capsys.readouterr().out
    assert "Searching for social apps on SER" in out
    assert "Listing third-party packages on SER" in out
    assert "Inspecting com.snapchat.android" in out
    assert apps and apps[0].package == "com.snapchat.android"
