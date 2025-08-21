# device/connect_to_device.py

from device import show_devices
from device.device_menu import interactive_device_menu
from utils.display_utils import error_utils
from utils.adb_utils.adb_devices import DeviceInfo
import utils.logging_utils.logging_engine as log


def select_device_from_list(devices: list[DeviceInfo]) -> DeviceInfo | None:
    """Prompt user to select a device from the list."""
    try:
        choice = int(input("\nEnter device number to connect: ").strip())
        if 1 <= choice <= len(devices):
            device = devices[choice - 1]
            log.info(f"User selected device {device.serial}")
            return device
        error_utils.handle_error("Invalid selection. Please choose a valid number.")
        log.warning("User selected an invalid device number")
        return None
    except ValueError:
        error_utils.handle_error("Invalid input. Please enter a number.")
        log.warning("User provided non-numeric input when selecting device")
        return None


def connect_to_device():
    """Entry point: list devices, let user pick, then launch device menu."""
    log.info("Listing devices for connection")
    devices = show_devices.display_selection_devices()
    if not devices:
        error_utils.handle_error("No devices available to connect.")
        log.warning("No connected devices discovered")
        return

    selected = select_device_from_list(devices)

    if selected:
        log.info(f"Connecting to device {selected.serial}")
        interactive_device_menu(selected)   # <-- now calls device_menu.py
    else:
        error_utils.handle_error("No valid device selected.")
        log.error("Device selection failed; aborting connection")
