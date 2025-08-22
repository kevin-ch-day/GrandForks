import shutil
from typing import Dict, Optional
import subprocess
import utils.logging_utils.logging_engine as log

def _run_local_command(cmd: list[str]) -> Optional[str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed: {' '.join(cmd)} :: {e.stderr.strip()}")
        return None
    except FileNotFoundError:
        log.error(f"Command not found: {cmd[0]}")
        return None

def analyze_apk(apk_path: str) -> Dict[str, str]:
    """Run aapt2 against ``apk_path`` and parse basic metadata."""

    print(f"Analyzing APK: {apk_path}")
    log.info(f"Static analysis requested for APK: {apk_path}")

    print("Checking for aapt2...")
    if not shutil.which("aapt2"):
        log.error("aapt2 not found. Install it via scripts/install-aapt2.sh")
        print("⚠️  aapt2 not found. Run scripts/install-aapt2.sh to enable APK analysis.")
        return {}

    print("Running aapt2 badging dump")
    output = _run_local_command(["aapt2", "dump", "badging", apk_path])
    if not output:
        print("⚠️  Failed to retrieve badging info")
        return {}

    print("Parsing badging output")

    metadata: Dict[str, str] = {}
    permissions: list[str] = []

    for line in output.splitlines():
        if line.startswith("package:"):
            for part in line.split():
                if "=" in part:
                    k, v = part.split("=", 1)
                    metadata[k] = v.strip("'")
        elif line.startswith("application-label:"):
            metadata["label"] = line.split(":", 1)[1].strip("'")
        elif line.startswith("uses-permission:"):
            permissions.append(line.split(":", 1)[1].strip("'"))

    if permissions:
        metadata["permissions"] = ", ".join(permissions)
        print(f"Found {len(permissions)} permission(s)")

    print("APK metadata extraction complete")
    return metadata

