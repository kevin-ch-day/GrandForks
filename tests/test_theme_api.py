import os
import io
import sys
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from utils.display_utils import theme


def strip_ansi(s: str) -> str:
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def test_color_and_style(monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    c = theme.color("fg.warning")
    assert "\x1b[" in c
    styled = theme.style("fg.warning", "bold")("boom")
    assert styled.startswith(c)
    assert styled.endswith("\x1b[0m")


def test_no_color_env(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert theme.color("fg.error") == ""
    monkeypatch.delenv("NO_COLOR")


def test_force_color_non_tty(monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert theme.color("fg.info") != ""
    monkeypatch.delenv("FORCE_COLOR")


def test_non_tty_disables(monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert theme.color("fg.info") == ""

