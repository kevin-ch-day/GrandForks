# utils/adb_utils/adb_ip_lookup.py
from utils.adb_utils import adb_runner
import utils.logging_utils.logging_engine as log
from typing import Optional


def get_ip_for_device(serial: str) -> Optional[str]:
    """
    Returns the IP address of a device if available.
    """
    result = adb_runner.run_adb_command(serial, ["shell", "ip", "addr", "show", "wlan0"])
    if not result.get("success", False):
        log.warning(f"ADB failed while retrieving IP for {serial} :: {result.get('error')}")
        return None

    output = result.get("output")
    if not isinstance(output, str) or not output:
        log.warning(f"No IP data returned for {serial}")
        return None

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("inet "):
            ip = line.split()[1].split("/")[0]  # "192.168.0.23/24" → "192.168.0.23"
            log.info(f"IP for {serial}: {ip}")
            return ip
    log.warning(f"No IP address found for {serial}")
    return None
