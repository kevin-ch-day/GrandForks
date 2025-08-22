from utils.adb_utils.adb_client import ADBClient
from utils.adb_utils import adb_runner


def test_list_devices(monkeypatch):
    def fake_run(serial, args, timeout=15, capture_stderr=False, log_errors=True):
        assert serial is None
        assert args == ['devices']
        out = 'List of devices attached\nX\tdevice\nY\tdevice\n'
        return {'success': True, 'output': out, 'error': ''}

    monkeypatch.setattr(adb_runner, 'run_adb_command', fake_run)

    devices = ADBClient.list_devices()
    assert devices == ['X', 'Y']


def test_shell_command(monkeypatch):
    calls = []

    def fake_run(serial, args, timeout=15, capture_stderr=False, log_errors=True):
        calls.append((serial, args))
        return {'success': True, 'output': 'ok', 'error': ''}

    monkeypatch.setattr(adb_runner, 'run_adb_command', fake_run)

    client = ADBClient('serial123')
    res = client.shell('id')
    assert res['success']
    assert calls == [('serial123', ['shell', 'id'])]
