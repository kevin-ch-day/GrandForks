import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from main_menu import MainMenu
from utils.test_utils.test_runner import PytestRunner


def test_run_tests_success(monkeypatch, capsys):
    called = {}

    class DummyResult:
        returncode = 0

    def fake_run(self):
        called['args'] = self.args
        return DummyResult()

    monkeypatch.setattr(PytestRunner, 'run', fake_run)
    MainMenu().run_test_suite()
    out = capsys.readouterr().out
    assert 'Running test suite' in out
    assert 'All tests passed' in out
    assert called['args'] == ['pytest']


def test_run_tests_failure(monkeypatch, capsys):
    class DummyResult:
        returncode = 1

    monkeypatch.setattr(PytestRunner, 'run', lambda self: DummyResult())
    MainMenu().run_test_suite()
    out = capsys.readouterr().out
    assert 'Some tests failed' in out
