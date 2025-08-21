import builtins
import sys

from utils.display_utils import prompt_utils, theme


def test_ask_yes_no_prompt_styled(monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    prompts = []

    def fake_input(p: str) -> str:
        prompts.append(p)
        return "y"

    monkeypatch.setattr(builtins, "input", fake_input)
    prompt_utils.ask_yes_no("Proceed?")

    prompt = prompts[0]
    assert theme.color("fg.emphasis") in prompt
    assert theme.color("fg.accent") in prompt


def test_ask_yes_no_confirmation(monkeypatch, capsys):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda _: "y")
    result = prompt_utils.ask_yes_no("Continue?")
    out = capsys.readouterr().out
    assert result is True
    assert theme.color("fg.success") in out
    assert "\x1b[1m" in out


def test_ask_yes_no_denial(monkeypatch, capsys):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda _: "n")
    result = prompt_utils.ask_yes_no("Continue?")
    out = capsys.readouterr().out
    assert result is False
    assert theme.color("fg.error") in out
    assert "\x1b[1m" in out
