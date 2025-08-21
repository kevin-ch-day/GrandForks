# analysis/static_analysis/package_analysis.py

from typing import List
import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_runner import run_adb_command


from typing import List, cast
import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_runner import run_adb_command


def list_installed_packages(serial: str) -> List[str]:
    """
    List installed packages on the connected device.

    Args:
        serial (str): Device serial number.

    Returns:
        List[str]: A list of installed package names.
    """
    log.info(f"Listing installed packages for {serial}")
    result = run_adb_command(serial, ["shell", "pm", "list", "packages"])

    if not result["success"]:
        log.warning(
            f"ADB failed while fetching package list for {serial} :: {result['error']}"
        )
        return []

    output = cast(str, result["output"])  # ✅ explicitly tell type checker this is str
    if not output:
        log.warning(f"No packages found on {serial}")
        return []

    return [line.replace("package:", "").strip() for line in output.splitlines()]



def _parse_permissions(dumpsys_output: str) -> List[str]:
    """
    Parse permissions from adb dumpsys output.

    Args:
        dumpsys_output (str): Raw adb output from `dumpsys package <pkg>`.

    Returns:
        List[str]: Extracted permissions.
    """
    perms = []
    for line in dumpsys_output.splitlines():
        line = line.strip()
        if line.startswith(("uses-permission:", "permission:")):
            perms.append(line.split(":")[-1].strip())
    return perms


def get_package_permissions(serial: str, package: str) -> List[str]:
    """
    Fetch declared permissions for a given package on the device.

    Args:
        serial (str): Device serial number.
        package (str): Package name.

    Returns:
        List[str]: A list of permissions used by the package.
    """
    log.info(f"Fetching permissions for {package} on {serial}")
    result = run_adb_command(serial, ["shell", "dumpsys", "package", package"])

    # Ensure command succeeded
    if not result.get("success", False):
        log.warning(
            f"ADB failed while fetching permissions for {package} on {serial} :: {result.get('error')}"
        )
        return []

    # Ensure output is a string
    output: Optional[str] = result.get("output")
    if not isinstance(output, str) or not output.strip():
        log.warning(f"No permission data found for {package} on {serial}")
        return []

    # Safe: output is now definitely a string
    return _parse_permissions(output)