import types

from scripts import adb_root as script
from utils.adb_utils.adb_devices import DeviceInfo


def test_main_with_explicit_serial(monkeypatch, capsys):
    called = {}

    def fake_attempt_root(serial):
        called['serial'] = serial
        return True

    monkeypatch.setattr(script, 'attempt_root', fake_attempt_root)
    exit_code = script.main(['SER123'])
    assert exit_code == 0
    assert called['serial'] == 'SER123'
    assert 'Root access granted' in capsys.readouterr().out


def test_main_uses_first_connected(monkeypatch, capsys):
    device = DeviceInfo(serial='SER456', state='device', model='m', type='Physical')
    monkeypatch.setattr(script, 'get_connected_devices', lambda: [device])

    called = {}

    def fake_attempt_root(serial):
        called['serial'] = serial
        return False

    monkeypatch.setattr(script, 'attempt_root', fake_attempt_root)
    exit_code = script.main([])
    assert exit_code == 1
    assert called['serial'] == 'SER456'
    assert 'Root access denied' in capsys.readouterr().out
