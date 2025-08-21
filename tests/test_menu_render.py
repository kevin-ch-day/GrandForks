import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from utils.display_utils import menu_utils, theme


def strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def dummy():
    pass


def test_menu_render(capsys):
    menu_utils.print_menu_header("Main")
    menu_utils.print_menu_options({"1": ("Start", dummy)}, "Exit")
    out = capsys.readouterr().out
    plain = strip_ansi(out)
    assert "Main" in plain
    assert "[1] Start" in plain
    assert "[0] Exit" in plain
    # hotkey should be accented
    assert theme.color("fg.accent")[:4] in out


def test_selected_option_emphasis(capsys):
    menu_utils.run_menu_action("Start", dummy)
    out = capsys.readouterr().out
    assert "Start" in out
    assert theme.color("fg.accent") in out


def test_highlight_inverse_with_arrow(capsys):
    menu_utils.print_menu_options({"1": ("Start", dummy)}, "Exit", highlight="1")
    out = capsys.readouterr().out
    assert "\x1b[7m" in out  # inverse video applied
    assert "▶ [1] Start" in strip_ansi(out)


def test_highlight_accent_style(capsys):
    menu_utils.print_menu_options(
        {"1": ("Start", dummy)}, "Exit", highlight="1", highlight_style="accent"
    )
    out = capsys.readouterr().out
    assert theme.color("fg.accent") in out
