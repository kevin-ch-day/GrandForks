"""Basic dynamic analysis implementation.

This module provides a very small subset of dynamic analysis features. It is
designed to run lightweight runtime checks against a connected Android device
using ``adb``.  At the moment it gathers a snapshot of ``logcat`` output and the
current activity stack and stores those results on disk.
"""

from pathlib import Path
from typing import Optional, Union

import utils.logging_utils.logging_engine as log
from utils.adb_utils.adb_runner import run_adb_command


def run_dynamic_analysis(
    serial: str,
    output_dir: Optional[Union[str, Path]] = None,
    duration: int = 15,
) -> dict[str, Path]:
    """Run simple dynamic analysis for a given device.

    Args:
        serial: The device serial identifier.
        output_dir: Directory where analysis artefacts are written.  If not
            provided ``dynamic_analysis`` will be created relative to the
            current working directory.
        duration: Maximum number of seconds to allow each adb command to run.

    Returns:
        Mapping of artefact names to the paths where they were written.
    """

    out_dir = Path(output_dir) if output_dir else Path("dynamic_analysis")
    out_dir.mkdir(parents=True, exist_ok=True)

    logcat_path = out_dir / "logcat.txt"
    activity_path = out_dir / "activity.txt"

    # Capture a snapshot of logcat
    logcat_res = run_adb_command(
        serial, ["logcat", "-d"], timeout=duration, log_errors=False
    )
    if logcat_res["success"]:
        logcat_path.write_text(logcat_res["output"])
    else:
        log.warning(logcat_res["error"])
        logcat_path.write_text("")

    # Capture the current activity stack
    activity_res = run_adb_command(
        serial,
        ["shell", "dumpsys", "activity", "activities"],
        timeout=duration,
        log_errors=False,
    )
    if activity_res["success"]:
        activity_path.write_text(activity_res["output"])
    else:
        log.warning(activity_res["error"])
        activity_path.write_text("")

    message = f"Dynamic analysis complete for {serial}"
    log.info(message)
    print(message)
    print(f"Logcat saved to {logcat_path}")
    print(f"Activity dump saved to {activity_path}")

    return {"logcat": logcat_path, "activity": activity_path}

