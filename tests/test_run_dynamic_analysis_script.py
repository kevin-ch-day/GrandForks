from pathlib import Path

from scripts import run_dynamic_analysis as script
from utils.adb_utils.adb_devices import DeviceInfo


def test_main_with_explicit_serial(monkeypatch):
    called = {}

    def fake_run_dynamic_analysis(serial, output_dir=None, duration=15):
        called['serial'] = serial
        called['output_dir'] = output_dir
        called['duration'] = duration

    monkeypatch.setattr(script, 'run_dynamic_analysis', fake_run_dynamic_analysis)
    exit_code = script.main(['--device', 'SER123', '-o', 'out', '-d', '20'])
    assert exit_code == 0
    assert called['serial'] == 'SER123'
    assert called['output_dir'] == Path('out')
    assert called['duration'] == 20


def test_main_uses_first_connected(monkeypatch):
    device = DeviceInfo(serial='SER456', state='device', model='m', type='Physical')
    monkeypatch.setattr(script, 'get_connected_devices', lambda: [device])

    called = {}

    def fake_run_dynamic_analysis(serial, output_dir=None, duration=15):
        called['serial'] = serial
        return {'logcat': Path('lc'), 'activity': Path('act')}

    monkeypatch.setattr(script, 'run_dynamic_analysis', fake_run_dynamic_analysis)
    exit_code = script.main([])
    assert exit_code == 0
    assert called['serial'] == 'SER456'


def test_main_errors_on_multiple(monkeypatch, capsys):
    devices = [
        DeviceInfo(serial='A', state='device', model='m', type='Physical'),
        DeviceInfo(serial='B', state='device', model='m', type='Physical'),
    ]
    monkeypatch.setattr(script, 'get_connected_devices', lambda: devices)
    exit_code = script.main([])
    assert exit_code == 1
    out = capsys.readouterr().out
    assert 'Multiple devices detected' in out

