from utils.adb_utils import adb_runner


def test_run_adb_command_errors_on_multiple(monkeypatch):
    def fake_execute(cmd, timeout=15, capture_stderr=False, log_errors=True):
        if cmd[:3] == ['adb', 'devices', '-l']:
            out = 'List of devices attached\nA\tdevice\nB\tdevice\n'
            return {'success': True, 'output': out, 'error': ''}
        return {'success': True, 'output': '', 'error': ''}

    monkeypatch.setattr(adb_runner, 'execute_command', fake_execute)
    monkeypatch.setattr(adb_runner, 'is_adb_available', lambda log_errors=True: True)

    res = adb_runner.run_adb_command(None, ['shell', 'id'])
    assert not res['success']
    assert 'Multiple devices' in res['error']
