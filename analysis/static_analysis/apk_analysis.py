import shutil
from typing import Dict, Optional
import utils.logging_utils.logging_engine as log
import subprocess

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
    log.info(f"Static analysis requested for APK: {apk_path}")

    if not shutil.which("aapt2"):
        log.error("aapt2 not found. Install it via scripts/install-aapt2.sh")
        print("⚠️  aapt2 not found. Run scripts/install-aapt2.sh to enable APK analysis.")
        return {}

    output = _run_local_command(["aapt2", "dump", "badging", apk_path])
    if not output:
        return {}

    metadata: Dict[str, str] = {}
    permissions = []
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
    return metadata
