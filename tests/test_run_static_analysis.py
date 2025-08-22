import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.static_analysis import run_static_analysis
from analysis.static_analysis.social_app_finder import SocialApp


def test_analyze_device_creates_output(monkeypatch, tmp_path, capsys):
    def fake_analyze_packages(serial, raw_dir=None):
        # Simulate writing raw outputs
        if raw_dir is not None:
            (raw_dir / 'dumpsys_package.txt').write_text('dump')
            (raw_dir / 'pm_list_packages.txt').write_text('pm')
        return [{'name': 'pkg', 'apk_path': '/a/b.apk', 'category': 'cat', 'risk_score': 0}]

    def fake_find_social(serial, raw_dir=None):
        if raw_dir is not None:
            (raw_dir / 'third_party_packages.txt').write_text('third')
        return [SocialApp('pkg', 'App', [], None, {})]

    def fake_run_adb_command(serial, args, timeout=60, log_errors=False):
        if args[0] == 'pull':
            Path(args[2]).write_text('apk')
        return {'success': True}

    monkeypatch.setattr(
        run_static_analysis.package_analysis,
        'analyze_packages',
        fake_analyze_packages,
    )
    monkeypatch.setattr(
        run_static_analysis.social_app_finder,
        'find_social_apps',
        fake_find_social,
    )
    monkeypatch.setattr(
        run_static_analysis.report_formatter,
        'print_reports',
        lambda reports, serial, limit: None,
    )
    monkeypatch.setattr(run_static_analysis, 'run_adb_command', fake_run_adb_command)
    monkeypatch.chdir(tmp_path)

    run_static_analysis.analyze_device('SER123', artifact_limit=1)
    out = capsys.readouterr().out
    assert 'Starting static analysis for device SER123' in out
    assert 'Run Dashboard' in out
    assert 'Social apps discovered' in out

    root = tmp_path / 'output' / 'SER123'
    runs = [p for p in root.iterdir() if p.is_dir() and p.name != 'latest']
    assert len(runs) == 1
    run_path = runs[0]
    assert (run_path / 'reports' / 'packages.csv').exists()
    assert (run_path / 'reports' / 'social_apps.csv').exists()
    assert (run_path / 'raw' / 'dumpsys_package.txt').exists()
    assert (run_path / 'raw' / 'pm_list_packages.txt').exists()
    assert (run_path / 'raw' / 'third_party_packages.txt').exists()
    assert (run_path / 'apks' / 'pkg.apk').exists()
    latest = root / 'latest'
    assert latest.is_symlink()
    assert latest.resolve() == run_path.resolve()


def test_analyze_device_skip_apk_pull(monkeypatch, tmp_path, capsys):
    def fake_analyze_packages(serial, raw_dir=None):
        if raw_dir is not None:
            (raw_dir / 'dumpsys_package.txt').write_text('dump')
        return [{'name': 'pkg', 'apk_path': '/a/b.apk', 'category': 'cat', 'risk_score': 0}]

    def fake_find_social(serial, raw_dir=None):
        return []

    called = {'pull': False}

    def fake_run_adb_command(serial, args, timeout=60, log_errors=False):
        if args[0] == 'pull':
            called['pull'] = True
        return {'success': True}

    monkeypatch.setattr(
        run_static_analysis.package_analysis,
        'analyze_packages',
        fake_analyze_packages,
    )
    monkeypatch.setattr(
        run_static_analysis.social_app_finder,
        'find_social_apps',
        fake_find_social,
    )
    monkeypatch.setattr(
        run_static_analysis.report_formatter,
        'print_reports',
        lambda reports, serial, limit: None,
    )
    monkeypatch.setattr(run_static_analysis, 'run_adb_command', fake_run_adb_command)
    monkeypatch.chdir(tmp_path)

    run_static_analysis.analyze_device('SER', pull_apk_files=False)
    out = capsys.readouterr().out
    assert 'Pulling APKs' not in out

    root = tmp_path / 'output' / 'SER'
    runs = [p for p in root.iterdir() if p.is_dir() and p.name != 'latest']
    run_path = runs[0]
    assert not (run_path / 'apks').exists()
    assert called['pull'] is False


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


def test_resolve_serial_multiple(monkeypatch, capsys):
    monkeypatch.setattr(run_static_analysis, 'get_connected_devices', lambda: [Dummy('A'), Dummy('B')])
    serial = run_static_analysis._resolve_serial(None)
    assert serial is None
    out = capsys.readouterr().out
    assert 'Multiple devices detected' in out


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
