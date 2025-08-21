import sys

from utils.display_utils import error_utils, theme


def test_show_messages_colored(monkeypatch, capsys):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    cases = [
        (error_utils.show_error, "fg.error"),
        (error_utils.show_warning, "fg.warning"),
        (error_utils.show_info, "fg.info"),
    ]
    for func, token in cases:
        func("test message")
        out = capsys.readouterr().out
        color = theme.color(token)
        lines = [line for line in out.splitlines() if line]
        assert color in lines[0]
        assert "\x1b[1m" in lines[0]
        assert color in lines[2]
        assert "\x1b[1m" in lines[2]
