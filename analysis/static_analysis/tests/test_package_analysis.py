import unittest
from pathlib import Path
from unittest.mock import patch
from typing import Dict

import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "analysis" / "static_analysis" / "package_analysis.py"
sys.path.append(str(ROOT))
spec = importlib.util.spec_from_file_location("package_analysis", MODULE_PATH)
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)  # type: ignore


class PackageAnalysisTests(unittest.TestCase):
    def _setup_mocks(
        self, dumpsys_output: str, pm_list_output: str, hash_map: Dict[str, str]
    ) -> patch:
        """Helper to patch run_adb_command with provided outputs."""

        def fake_run_adb_command(serial, cmd):
            if cmd == ["shell", "dumpsys", "package"]:
                return {"success": True, "output": dumpsys_output}
            if cmd == [
                "shell",
                "pm",
                "list",
                "packages",
                "-f",
                "-u",
                "--user",
                "0",
            ]:
                return {"success": True, "output": pm_list_output}
            if len(cmd) == 3 and cmd[0] == "shell" and cmd[1] == "sha256sum":
                path = cmd[2]
                hash_val = hash_map.get(path, "")
                return {"success": True, "output": f"{hash_val} {path}"}
            return {"success": False, "error": "unsupported"}

        return patch.object(pa, "run_adb_command", side_effect=fake_run_adb_command)

    def test_analyze_packages_with_valid_apks(self):
        dumpsys_output = (
            "Package [com.example.one]\n"
            "  uses-permission: android.permission.READ_SMS\n"
            "Package [com.example.two]\n"
            "  uses-permission: android.permission.ACCESS_FINE_LOCATION\n"
        )
        pm_list_output = (
            "package:/data/app/com.example.one-1/base.apk=com.example.one\n"
            "package:/data/app/com.example.two-1/base.apk=com.example.two\n"
        )
        hash_map = {
            "/data/app/com.example.one-1/base.apk": "hashone",
            "/data/app/com.example.two-1/base.apk": "hashtwo",
        }

        with self._setup_mocks(dumpsys_output, pm_list_output, hash_map):
            reports = pa.analyze_packages("ABC123")

        self.assertEqual(len(reports), 2)
        names = {r.name for r in reports}
        self.assertIn("com.example.one", names)
        self.assertIn("com.example.two", names)
        risk_map = {r.name: r.risk_score for r in reports}
        self.assertEqual(risk_map["com.example.one"], 1)
        self.assertEqual(risk_map["com.example.two"], 1)
        hash_results = {r.name: r.apk_hash for r in reports}
        self.assertEqual(hash_results["com.example.one"], "hashone")
        self.assertEqual(hash_results["com.example.two"], "hashtwo")

    def test_analyze_packages_with_missing_apk(self):
        dumpsys_output = (
            "Package [com.example.one]\n"
            "  uses-permission: android.permission.READ_SMS\n"
            "Package [com.example.two]\n"
            "  uses-permission: android.permission.ACCESS_FINE_LOCATION\n"
        )
        pm_list_output = (
            "package:/data/app/com.example.one-1/base.apk=com.example.one\n"
        )
        hash_map = {"/data/app/com.example.one-1/base.apk": "hashone"}

        with self._setup_mocks(dumpsys_output, pm_list_output, hash_map):
            reports = pa.analyze_packages("ABC123")

        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].name, "com.example.one")
        self.assertEqual(reports[0].apk_hash, "hashone")

    def test_analyze_packages_with_no_packages(self):
        dumpsys_output = ""
        pm_list_output = ""
        hash_map = {}

        with self._setup_mocks(dumpsys_output, pm_list_output, hash_map):
            reports = pa.analyze_packages("ABC123")

        self.assertEqual(reports, [])


if __name__ == "__main__":
    unittest.main()
