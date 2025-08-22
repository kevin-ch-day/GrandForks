import subprocess
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from utils import csv_utils


def run_cli(tmp_path, rows, pm_lines):
    csv_path = tmp_path / "apk_list.csv"
    csv_utils.write_csv(csv_path, rows, headers=[])
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    pm_file = raw_dir / "pm_list_packages.txt"
    pm_file.write_text("\n".join(pm_lines) + "\n", encoding="utf-8")
    run_script = repo_root / "run.sh"
    result = subprocess.run(
        [str(run_script), "--validate", str(csv_path)],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    return result


def test_cli_validate_reports_mismatch(tmp_path):
    rows = [{"Package": "com.example", "APK_Path": "/a.apk"}]
    result = run_cli(tmp_path, rows, ["pkg1", "pkg2"])
    assert result.returncode == 1
    assert "Package count mismatch" in result.stdout


def test_cli_validate_reports_match(tmp_path):
    rows = [
        {"Package": "com.example1", "APK_Path": "/a.apk"},
        {"Package": "com.example2", "APK_Path": "/b.apk"},
    ]
    result = run_cli(tmp_path, rows, ["pkg1", "pkg2"])
    assert result.returncode == 0
    assert "Package counts match" in result.stdout
