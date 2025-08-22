"""High level ADB client built on top of :mod:`adb_runner` utilities.

This module provides an object-oriented interface for common ADB
operations.  It delegates command execution to
:func:`utils.adb_utils.adb_runner.run_adb_command` which already
implements device selection, readiness checks and logging.  The class
exposes convenience methods for frequently used ADB commands to keep the
rest of the codebase tidy and expressive.
"""

from __future__ import annotations

from typing import List, Dict, Optional, Union
import subprocess

from . import adb_runner


Result = Dict[str, Union[bool, str]]


class ADBClient:
    """Simple wrapper around the raw ADB command utilities.

    Parameters
    ----------
    serial:
        Optional device serial.  When omitted, commands that require a
        target device will attempt auto-discovery in
        :func:`adb_runner.run_adb_command`.
    """

    def __init__(self, serial: Optional[str] = None) -> None:
        self.serial = serial

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------
    @staticmethod
    def list_devices() -> List[str]:
        """Return a list of attached device serials."""
        res = adb_runner.run_adb_command(None, ["devices"])
        if not res.get("success"):
            return []
        lines = [l for l in res.get("output", "").splitlines()[1:] if l.strip()]
        return [l.split()[0] for l in lines]

    # ------------------------------------------------------------------
    # Core execution helpers
    # ------------------------------------------------------------------
    def ensure_ready(self) -> Result:
        """Ensure the device is connected and in a "device" state."""
        if not self.serial:
            return {"success": False, "output": "", "error": "No device serial specified"}
        return adb_runner.ensure_device_ready(self.serial)

    def run(self, args: List[str], **kwargs) -> Result:
        """Run an arbitrary adb command for the configured serial."""
        return adb_runner.run_adb_command(self.serial, args, **kwargs)

    # ------------------------------------------------------------------
    # High level convenience methods
    # ------------------------------------------------------------------
    def shell(self, command: str) -> Result:
        """Execute a non-interactive shell command."""
        return self.run(["shell", command])

    def interactive_shell(self) -> Result:
        """Open an interactive shell session for the device."""
        ready = self.ensure_ready()
        if not ready.get("success"):
            return ready
        subprocess.run(["adb", "-s", self.serial, "shell"])
        return {"success": True, "output": "", "error": ""}

    def reboot(self) -> Result:
        """Reboot the device."""
        return self.run(["reboot"])

    def install_apk(self, apk_path: str) -> Result:
        """Install an APK onto the device."""
        return self.run(["install", apk_path])

    def push(self, local: str, remote: str) -> Result:
        """Push a file from local to remote path."""
        return self.run(["push", local, remote])

    def pull(self, remote: str, local: str) -> Result:
        """Pull a file from the device."""
        return self.run(["pull", remote, local])
