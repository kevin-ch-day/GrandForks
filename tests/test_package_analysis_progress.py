import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.static_analysis import package_analysis


def test_analyze_packages_shows_steps(monkeypatch, capsys):
    monkeypatch.setattr(
        package_analysis,
        'get_all_package_permissions',
        lambda s, raw_dir=None: {'pkg': []},
    )
    monkeypatch.setattr(
        package_analysis,
        'get_installed_apk_paths',
        lambda s, raw_dir=None: {'pkg': 'path.apk'},
    )
    monkeypatch.setattr(
        package_analysis,
        'verify_package_apks',
        lambda packages, paths: (paths, []),
    )
    monkeypatch.setattr(
        package_analysis, 'compute_apk_hashes', lambda serial, apk_map: {'pkg': 'hash'}
    )
    monkeypatch.setattr(package_analysis, 'string_finder', None)

    reports = package_analysis.analyze_packages('SER')
    out = capsys.readouterr().out
    assert "Retrieving package permissions" in out
    assert "Listing installed APK paths" in out
    assert "Verifying APK availability" in out
    assert "Computing APK hashes" in out
    assert len(reports) == 1
