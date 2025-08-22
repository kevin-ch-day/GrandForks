import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from analysis.static_analysis import secret_scanner


def test_scan_reports_hits(capsys):
    text = "AKIA1234567890ABCDEF token=abcdefghi"
    results = secret_scanner.scan(text)
    out = capsys.readouterr().out
    assert "Scanning text for secret patterns" in out
    assert "aws_access_key" in out
    assert "generic_secret" in out
    assert "Secret scan complete" in out
    assert "aws_access_key" in results
    assert "generic_secret" in results
