import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.static_analysis import run_static_analysis
from analysis.static_analysis.social_app_finder import SocialApp


def test_analyze_device_shows_progress(monkeypatch, capsys):
    monkeypatch.setattr(
        run_static_analysis.package_analysis,
        'analyze_packages',
        lambda serial: [{'package': 'com.example'}],
    )

    def fake_print_reports(reports, serial, limit):
        pass

    monkeypatch.setattr(
        run_static_analysis.report_formatter,
        'print_reports',
        fake_print_reports,
    )

    run_static_analysis.analyze_device('SER123', artifact_limit=1)
    out = capsys.readouterr().out
    assert 'Starting static analysis for device SER123' in out
    assert 'Gathering packages from device' in out
    assert 'Analyzing 1 package' in out


def test_analyze_apk_driver_shows_metadata(monkeypatch, capsys):
    monkeypatch.setattr(
        run_static_analysis.apk_analysis,
        'analyze_apk',
        lambda path: {'size': '123'},
    )
    run_static_analysis.analyze_apk_driver('example.apk')
    out = capsys.readouterr().out
    assert 'Scanning APK at example.apk' in out
    assert 'size' in out


def test_list_apk_hashes_verbose(monkeypatch, capsys):
    monkeypatch.setattr(
        run_static_analysis.package_analysis,
        'get_installed_apk_paths',
        lambda serial: {'pkg': 'path.apk'},
    )
    monkeypatch.setattr(
        run_static_analysis.package_analysis,
        'compute_apk_hashes',
        lambda serial, apk_map: {'pkg': 'abc123'},
    )
    run_static_analysis.list_apk_hashes('SER123')
    out = capsys.readouterr().out
    assert 'Retrieving APK paths from SER123' in out
    assert 'Found 1 package' in out
    assert 'pkg' in out


def test_validate_apk_path_checks_extension(tmp_path, capsys):
    valid = tmp_path / 'good.apk'
    valid.touch()
    invalid = tmp_path / 'bad.txt'
    invalid.touch()

    assert run_static_analysis.validate_apk_path(str(valid)) is True
    out = capsys.readouterr().out
    assert out == ''

    assert run_static_analysis.validate_apk_path(str(invalid)) is False
    out = capsys.readouterr().out
    assert 'not an APK file' in out

    assert run_static_analysis.validate_apk_path(str(tmp_path / 'missing.apk')) is False
    out = capsys.readouterr().out
    assert 'APK not found' in out


class Dummy:
    def __init__(self, serial: str):
        self.serial = serial
        self.model = 'm'


def test_resolve_serial_rejects_unknown(monkeypatch, capsys):
    monkeypatch.setattr(run_static_analysis, 'get_connected_devices', lambda: [Dummy('A')])
    serial = run_static_analysis._resolve_serial('B')
    assert serial is None
    out = capsys.readouterr().out
    assert 'not connected' in out


def test_scan_package_strings_reports_artifacts(monkeypatch, capsys):
    monkeypatch.setattr(run_static_analysis.string_finder, 'find_artifacts', lambda s, p: ['hit'])
    monkeypatch.setattr(run_static_analysis.string_finder, 'print_failure_summary', lambda: None)
    run_static_analysis.scan_package_strings('SER', 'pkg')
    out = capsys.readouterr().out
    assert 'Scanning pkg on SER' in out
    assert 'Found 1 potential artifact' in out
    assert 'hit' in out


def test_list_social_apps_reports(monkeypatch, capsys):
    monkeypatch.setattr(
        run_static_analysis.social_app_finder,
        'find_social_apps',
        lambda serial: [SocialApp('pkg', 'App', [], None, {})],
    )
    run_static_analysis.list_social_apps('SER')
    out = capsys.readouterr().out
    assert 'Searching for social apps on SER' in out
    assert 'pkg (App)' in out
