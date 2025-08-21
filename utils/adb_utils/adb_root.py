# utils/adb_utils/adb_root.py
"""Utilities to attempt to gain root access on a device."""

from utils.adb_utils import adb_runner
import utils.logging_utils.logging_engine as log


def is_device_rooted(serial: str) -> bool:
    """Return True if the device shell reports uid=0."""
    result = adb_runner.run_adb_command(serial, ["shell", "id"], timeout=10, log_errors=False)
    if not result.get("success"):
        return False
    output = result.get("output", "")
    return "uid=0" in output


def attempt_root(serial: str) -> bool:
    """Attempt to restart adbd as root and verify access."""
    log.info(f"Attempting adb root for {serial}")
    res = adb_runner.run_adb_command(serial, ["root"], timeout=10)
    if not res.get("success"):
        log.warning(f"adb root failed for {serial} :: {res.get('error')}")
        return False
    if is_device_rooted(serial):
        log.info(f"Root access granted on {serial}")
        return True
    log.warning(f"Root access denied on {serial}")
    return False

