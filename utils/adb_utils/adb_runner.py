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
    cmd: List[str],
    timeout: int = 15,
    capture_stderr: bool = False,
    log_errors: bool = True,
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
    log.debug(f"[EXECUTE] Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        snippet = output if len(output) <= 200 else f"{output[:200]}..."
        log.debug(f"[EXECUTE] Output: {snippet}")
        return {"success": True, "output": output, "error": ""}

    except subprocess.TimeoutExpired:
        msg = f"Command timed out after {timeout}s: {' '.join(cmd)}"
        if log_errors:
            log.error(msg)
        return {"success": False, "output": "", "error": msg}

    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip() if e.stderr else str(e)
        msg = f"Command failed: {' '.join(cmd)} :: {err_msg}"
        if log_errors:
            log.error(msg)
        return {
            "success": False,
            "output": e.stderr.strip() if capture_stderr else "",
            "error": msg,
        }

    except FileNotFoundError:
        msg = f"Command not found: {cmd[0]}"
        if log_errors:
            log.error(msg)
        return {"success": False, "output": "", "error": msg}


def is_adb_available(log_errors: bool = True) -> bool:
    """Check if adb is available in PATH."""
    if shutil.which("adb"):
        return True
    if log_errors:
        log.error("adb not found in PATH")
    return False


def ensure_device_ready(serial: str) -> Dict[str, Union[bool, str]]:
    """Block until the given device is ready for adb commands."""

    wait_res = execute_command(["adb", "-s", serial, "wait-for-device"])
    if not wait_res.get("success"):
        return wait_res

    state_res = execute_command(["adb", "-s", serial, "get-state"])
    if not state_res.get("success"):
        return state_res

    state = state_res.get("output", "").strip()
    if state != "device":
        msg = f"Device {serial} not ready (state: {state})"
        log.error(msg)
        return {"success": False, "output": state, "error": msg}

    return {"success": True, "output": state, "error": ""}


def run_adb_command(
    serial: Optional[str],
    args: List[str],
    timeout: int = 15,
    capture_stderr: bool = False,
    log_errors: bool = True,
) -> Dict[str, Union[bool, str]]:
    """
    Run an adb command for a specific device.

    Returns a dict with success, output, error.
    """
    if not is_adb_available(log_errors=log_errors):
        return {"success": False, "output": "", "error": "adb not found"}

    needs_device = args and args[0] != "devices"

    if needs_device and serial is None:
        devices_res = execute_command(["adb", "devices", "-l"], log_errors=log_errors)
        if not devices_res.get("success"):
            return devices_res
        lines = [l for l in devices_res.get("output", "").splitlines()[1:] if l.strip()]
        if len(lines) > 1:
            msg = "Multiple devices connected. Use --device to specify one."
            if log_errors:
                log.error(msg)
            return {"success": False, "output": "", "error": msg}
        if len(lines) == 0:
            msg = "No adb devices connected"
            if log_errors:
                log.error(msg)
            return {"success": False, "output": "", "error": msg}
        serial = lines[0].split()[0]

    if needs_device and serial:
        ready = ensure_device_ready(serial)
        if not ready.get("success"):
            return ready

    cmd = build_adb_command(serial, args)
    return execute_command(
        cmd,
        timeout=timeout,
        capture_stderr=capture_stderr,
        log_errors=log_errors,
    )
