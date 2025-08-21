# device/connect_to_device.py

from device import show_devices
from device.device_menu import interactive_device_menu
from utils.display_utils import error_utils


def select_device_from_list(devices: list[dict]) -> dict | None:
    """Prompt user to select a device from the list."""
    try:
        choice = int(input("\nEnter device number to connect: ").strip())
        if 1 <= choice <= len(devices):
            return devices[choice - 1]
        error_utils.handle_error("Invalid selection. Please choose a valid number.")
        return None
    except ValueError:
        error_utils.handle_error("Invalid input. Please enter a number.")
        return None


def connect_to_device():
    """Entry point: list devices, let user pick, then launch device menu."""
    devices = show_devices.get_connected_devices()
    if not devices or ("error" in devices[0]):
        error_utils.handle_error("No devices available to connect.")
        return

    show_devices.display_selection_devices()
    selected = select_device_from_list(devices)

    if selected:
        interactive_device_menu(selected)   # <-- now calls device_menu.py
    else:
        error_utils.handle_error("No valid device selected.")
