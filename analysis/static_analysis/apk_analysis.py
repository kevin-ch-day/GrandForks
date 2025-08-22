import re
import shlex
import shutil
from typing import Dict, Optional
import subprocess
import utils.logging_utils.logging_engine as log


def _run_local_command(cmd: list[str]) -> Optional[str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed: {shlex.join(cmd)} :: {e.stderr.strip()}")
        return None
    except FileNotFoundError:
        log.error(f"Command not found: {cmd[0]}")
        return None


def analyze_apk(apk_path: str) -> Dict[str, str]:
    """
    Run a lightweight static analysis of an APK using aapt2/aapt badging output.

    Returns a dict of string metadata (e.g., package name, label, versionCode, versionName, permissions).
    'permissions' is a comma-separated string to preserve the Dict[str, str] annotation.
    """
    log.info(f"Static analysis requested for APK: {apk_path}")

    # Prefer aapt2, fall back to aapt
    aapt_bin = shutil.which("aapt2") or shutil.which("aapt")
    if not aapt_bin:
        msg = "aapt2/aapt not found. Install it via scripts/install-aapt2.sh"
        log.error(msg)
        print(f"⚠️  {msg}")
        return {}

    output = _run_local_command([aapt_bin, "dump", "badging", apk_path])
    if not output:
        return {}

    metadata: Dict[str, str] = {}
    permissions_set: set[str] = set()

    # Precompiled regexes for accuracy
    re_pkg = re.compile(r"^package:\s+(.*)$")
    re_kv = re.compile(r"(\w+)='([^']*)'")
    re_label_any = re.compile(r"^application-label(?::|'|-([a-z]{2})(?:-[A-Z]{2})?)?:'([^']*)'")
    re_perm = re.compile(r"^uses-permission(?:-sdk-?\d*)?:\s*(.*)$")
    re_perm_name = re.compile(r"name='([^']+)'")

    for raw_line in output.splitlines():
        line = raw_line.strip()

        # package line: parse key='value' pairs
        m_pkg = re_pkg.match(line)
        if m_pkg:
            for k, v in re_kv.findall(m_pkg.group(1)):
                # e.g., name, versionCode, versionName, platformBuildVersionName, etc.
                metadata[k] = v
            continue

        # application label (default or locale-specific)
        m_label = re_label_any.match(line)
        if m_label:
            # Group 2 (index 2) is the label; group 1 (index 1) is optional locale
            label_value = m_label.group(2)
            # Prefer default label if present, else first locale-specific one
            if "label" not in metadata:
                metadata["label"] = label_value
            continue

        # permissions: extract name='...'
        m_perm = re_perm.match(line)
        if m_perm:
            perm_blob = m_perm.group(1)
            m_name = re_perm_name.search(perm_blob)
            if m_name:
                permissions_set.add(m_name.group(1))
            else:
                # Fallback: try to take the quoted segment if present
                m_any = re_kv.search(perm_blob)
                if m_any:
                    permissions_set.add(m_any.group(2))
            continue

        # sdkVersion / targetSdkVersion convenience
        if line.startswith("sdkVersion:'"):
            metadata["sdkVersion"] = line.split(":", 1)[1].strip("'")
            continue
        if line.startswith("targetSdkVersion:'"):
            metadata["targetSdkVersion"] = line.split(":", 1)[1].strip("'")
            continue

    if permissions_set:
        # Keep return type stable: comma-separated string
        metadata["permissions"] = ", ".join(sorted(permissions_set))

    return metadata
