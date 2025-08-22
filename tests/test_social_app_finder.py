import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.static_analysis import social_app_finder


def test_find_social_apps_reports(monkeypatch, capsys):
    def fake_list_packages(serial, apk_csv="apk_list.csv"):
        return {"com.snapchat.android": "/data/app/com.snapchat.android/base.apk"}, "csv"

    monkeypatch.setattr(social_app_finder.discovery, "list_packages", fake_list_packages)
    apps = social_app_finder.find_social_apps("SER")
    out = capsys.readouterr().out
    assert "Searching for social apps on SER" in out
    assert "Loaded 1 package(s) from csv" in out
    assert "Inspecting com.snapchat.android" in out
    assert apps and apps[0].package == "com.snapchat.android"


def test_find_social_apps_adb_lookup_success(monkeypatch, capsys):
    def fake_list_packages(serial, apk_csv="apk_list.csv"):
        return {"com.snapchat.android": ""}, "csv"

    def fake_run_adb_command(serial, args, **kwargs):
        if args[:2] == ["pm", "path"]:
            return {
                "success": True,
                "output": "package:/data/app/com.snapchat.android/base.apk",
                "error": "",
            }
        return {"success": False, "output": "", "error": ""}

    monkeypatch.setattr(social_app_finder.discovery, "list_packages", fake_list_packages)
    monkeypatch.setattr(social_app_finder, "run_adb_command", fake_run_adb_command)
    apps = social_app_finder.find_social_apps("SER")
    out = capsys.readouterr().out
    assert "Package com.snapchat.android missing path; checking adb" in out
    assert "pm path found /data/app/com.snapchat.android/base.apk" in out
    assert apps[0].apk_paths == ["/data/app/com.snapchat.android/base.apk"]


def test_find_social_apps_adb_lookup_failure(monkeypatch, capsys):
    def fake_list_packages(serial, apk_csv="apk_list.csv"):
        return {"com.snapchat.android": ""}, "csv"

    def fake_run_adb_command(serial, args, **kwargs):
        return {"success": True, "output": "", "error": ""}

    monkeypatch.setattr(social_app_finder.discovery, "list_packages", fake_list_packages)
    monkeypatch.setattr(social_app_finder, "run_adb_command", fake_run_adb_command)
    apps = social_app_finder.find_social_apps("SER")
    out = capsys.readouterr().out
    assert "pm path failed; searching common partitions" in out
    assert "Unresolved packages" in out
    assert apps[0].apk_paths == []
