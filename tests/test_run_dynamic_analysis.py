import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.dynamic_analysis.run_dynamic_analysis import run_dynamic_analysis


def test_run_dynamic_analysis_placeholder(capsys):
    run_dynamic_analysis("serial123")
    out = capsys.readouterr().out.strip()
    assert out == "Dynamic analysis not yet implemented for serial123"
