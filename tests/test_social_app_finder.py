import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.static_analysis import social_app_finder as saf


def test_parse_package_listing():
    sample = (
        "package:/data/app/abc/base.apk=com.zhiliaoapp.musically\n"
        "package:/data/app/def/base.apk=com.random.app\n"
        "package:/data/app/ghi/base.apk=com.instagram.android\n"
    )
    parsed = saf._parse_package_listing(sample)
    assert parsed["com.zhiliaoapp.musically"] == "/data/app/abc/base.apk"
    assert parsed["com.instagram.android"] == "/data/app/ghi/base.apk"
    assert "com.random.app" in parsed


def test_find_social_apps(monkeypatch):
    # Prepare fake adb responses
    def fake_run(serial, args, **kwargs):
        if args == ["shell", "pm", "list", "packages", "-f", "-3"]:
            output = (
                "package:/data/app/a/base.apk=com.zhiliaoapp.musically\n"
                "package:/data/app/b/base.apk=com.instagram.android\n"
                "package:/data/app/c/base.apk=com.other.app\n"
            )
            return {"success": True, "output": output}
        if args == ["shell", "pm", "path", "com.zhiliaoapp.musically"]:
            return {"success": True, "output": "package:/data/app/a/base.apk"}
        if args == ["shell", "pm", "path", "com.instagram.android"]:
            return {"success": True, "output": "package:/data/app/b/base.apk"}
        if args == ["shell", "dumpsys", "package", "com.zhiliaoapp.musically"]:
            return {
                "success": True,
                "output": (
                    "application-label: TikTok\n"
                    "versionName=1.2.3\nversionCode=123\n"
                    "installerPackageName=com.android.vending\nuid=1001"
                ),
            }
        if args == ["shell", "dumpsys", "package", "com.instagram.android"]:
            return {
                "success": True,
                "output": (
                    "application-label: Instagram\n"
                    "versionName=9.9.9\nversionCode=999\n"
                    "installerPackageName=com.android.vending\nuid=2002"
                ),
            }
        return {"success": False, "output": "", "error": "unexpected command"}

    monkeypatch.setattr(saf, "run_adb_command", fake_run)

    apps = saf.find_social_apps("SERIAL")
    assert {app.package for app in apps} == {
        "com.zhiliaoapp.musically",
        "com.instagram.android",
    }
    tiktok = next(a for a in apps if a.package == "com.zhiliaoapp.musically")
    assert tiktok.app_name == "TikTok"
    assert tiktok.label == "TikTok"
    assert tiktok.metadata["versionName"] == "1.2.3"
    assert "uid" in tiktok.metadata
