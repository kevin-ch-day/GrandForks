import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.static_analysis import apk_analysis


def test_analyze_apk_reports_steps(monkeypatch, capsys):
    monkeypatch.setattr(apk_analysis.shutil, 'which', lambda cmd: True)
    sample = "\n".join(
        [
            "package: name='com.example'",
            "application-label:'Example'",
            "uses-permission:'android.permission.INTERNET'",
        ]
    )
    monkeypatch.setattr(apk_analysis, '_run_local_command', lambda cmd: sample)
    meta = apk_analysis.analyze_apk('example.apk')
    out = capsys.readouterr().out
    assert 'Analyzing APK: example.apk' in out
    assert 'Checking for aapt2' in out
    assert 'Running aapt2 badging dump' in out
    assert 'Parsing badging output' in out
    assert 'Found 1 permission' in out
    assert 'APK metadata extraction complete' in out
    assert meta['name'] == 'com.example'
