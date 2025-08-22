import csv
from utils import csv_utils
from analysis.static_analysis import report_formatter


class DummyReport:
    def __init__(self, name, apk_path, category, risk_score):
        self.name = name
        self.apk_path = apk_path
        self.category = category
        self.risk_score = risk_score


def test_write_csv_sorts_and_enforces_headers(tmp_path):
    path = tmp_path / "out.csv"
    rows = [
        {"Package": "bbb", "APK_Path": "/b", "Extra": "2"},
        {"Package": "Aaa", "APK_Path": "/a", "Extra": "1"},
    ]
    csv_utils.write_csv(path, rows, headers=["Extra"])
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    assert lines[0] == "Package,APK_Path,Extra"
    assert lines[1].startswith("Aaa")
    assert content.endswith("\n")
    assert "\r\n" not in content


def test_read_and_validate_apk_list(tmp_path):
    path = tmp_path / "apk_list.csv"
    rows = [{"Package": "com.example", "APK_Path": "/a.apk"}]
    csv_utils.write_csv(path, rows, headers=[])
    assert csv_utils.validate_apk_list(path)
    read_rows = csv_utils.read_apk_list(path)
    assert read_rows == rows

    invalid = tmp_path / "bad.csv"
    invalid.write_text("Wrong,Header\n", encoding="utf-8")
    assert not csv_utils.validate_apk_list(invalid)

    invalid2 = tmp_path / "bad2.csv"
    invalid2.write_text("Package,APK_Path\npkg,\n", encoding="utf-8")
    assert not csv_utils.validate_apk_list(invalid2)


def test_report_formatter_writes_valid_csv(tmp_path):
    path = tmp_path / "apk_list.csv"
    reports = [DummyReport("com.app", "/app.apk", "util", 5)]
    report_formatter.write_csv_report(reports, path)
    assert csv_utils.validate_apk_list(path)
    rows = csv_utils.read_apk_list(path)
    assert rows[0]["Package"] == "com.app"
