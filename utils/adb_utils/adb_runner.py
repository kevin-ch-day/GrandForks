# utils/adb_utils/adb_runner.py
"""ADB command helper utilities."""

import shutil
import subprocess
from typing import Optional, List, Dict, Union
import utils.logging_utils.logging_engine as log


def build_adb_command(serial: Optional[str], args: List[str]) -> List[str]:
    """
    Build a full adb command with optional serial targeting.
    """
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    return cmd + args


def execute_command(
    cmd: List[str], timeout: int = 15, capture_stderr: bool = False
) -> Dict[str, Union[bool, str]]:
    """
    Execute a shell command with error handling and logging.

    Returns:
        dict: {
            "success": bool,
            "output": str (stdout or stderr if capture_stderr),
            "error": str (error message if failed)
        }
    """
    log.info(f"[EXECUTE] Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        log.debug(f"[EXECUTE] Output: {output[:200]}...")
        return {"success": True, "output": output, "error": ""}

    except subprocess.TimeoutExpired:
        msg = f"Command timed out after {timeout}s: {' '.join(cmd)}"
        log.error(msg)
        return {"success": False, "output": "", "error": msg}

    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip() if e.stderr else str(e)
        msg = f"Command failed: {' '.join(cmd)} :: {err_msg}"
        log.error(msg)
        return {
            "success": False,
            "output": e.stderr.strip() if capture_stderr else "",
            "error": msg,
        }

    except FileNotFoundError:
        msg = f"Command not found: {cmd[0]}"
        log.error(msg)
        return {"success": False, "output": "", "error": msg}


def is_adb_available() -> bool:
    """Check if adb is available in PATH."""
    if shutil.which("adb"):
        return True
    log.error("adb not found in PATH")
    return False


def run_adb_command(
    serial: Optional[str], args: List[str], timeout: int = 15, capture_stderr: bool = False
) -> Dict[str, Union[bool, str]]:
    """
    Run an adb command for a specific device.

    Returns a dict with success, output, error.
    """
    if not is_adb_available():
        return {"success": False, "output": "", "error": "adb not found"}

    cmd = build_adb_command(serial, args)
    return execute_command(cmd, timeout=timeout, capture_stderr=capture_stderr)
