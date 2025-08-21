import pytest

from utils.adb_utils import adb_root


def test_is_device_rooted_true(monkeypatch):
    def fake_run(serial, args, timeout=10, log_errors=False):
        assert args == ["shell", "id"]
        return {"success": True, "output": "uid=0(root) gid=0(root)"}

    monkeypatch.setattr(adb_root.adb_runner, "run_adb_command", fake_run)
    assert adb_root.is_device_rooted("serial")


def test_attempt_root_success(monkeypatch):
    calls = []

    def fake_run(serial, args, timeout=10, log_errors=True):
        calls.append(args)
        if args == ["root"]:
            return {"success": True, "output": "restarting adbd as root"}
        if args == ["shell", "id"]:
            return {"success": True, "output": "uid=0(root)"}
        return {"success": False, "error": "unexpected"}

    monkeypatch.setattr(adb_root.adb_runner, "run_adb_command", fake_run)
    assert adb_root.attempt_root("serial")
    assert calls[0] == ["root"]


def test_attempt_root_failure(monkeypatch):
    def fake_run(serial, args, timeout=10, log_errors=True):
        if args == ["root"]:
            return {"success": False, "error": "error"}
        return {"success": False, "error": "unexpected"}

    monkeypatch.setattr(adb_root.adb_runner, "run_adb_command", fake_run)
    assert not adb_root.attempt_root("serial")
