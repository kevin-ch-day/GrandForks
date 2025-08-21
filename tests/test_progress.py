import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from utils.display_utils import theme


def strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def test_progress_basic():
    p = theme.progress(2, 4, width=10)
    assert strip_ansi(p) == "[#####-----] 2/4"


def test_progress_complete():
    p = theme.progress(4, 4, width=8)
    assert strip_ansi(p) == "[########] 4/4"

