# main_menu.py
"""Centralized main menu using an object-oriented design."""

from config import app_config
from menus.base import BaseMenu, MenuAction
from utils.display_utils import error_utils
import utils.logging_utils.logging_engine as log
from device import show_devices, connect_to_device
from utils.about_app import about_app
from database.db_menu import DatabaseMenu
from utils.test_utils.test_runner import PytestRunner


class MainMenu(BaseMenu):
    """Primary application menu."""

    def __init__(self) -> None:
        super().__init__(
            title=f"{app_config.APP_NAME} v{app_config.APP_VERSION}",
            exit_label="Exit",
            highlight_choice="1",
            highlight_style="accent",
        )
        self.actions = {
            "1": MenuAction("Show Connected Devices", self.show_connected_devices),
            "2": MenuAction("Connect to a Device", self.connect_to_device),
            "3": MenuAction("Database", self.open_database_menu),
            "4": MenuAction("Run Test Suite", self.run_test_suite),
            "5": MenuAction("About App", about_app),
        }

    # ----- Menu Action Methods -----
    def show_connected_devices(self) -> None:
        """List all connected Android devices."""
        log.info("Selected: Show Connected Devices")
        try:
            show_devices.display_detailed_devices()
        except KeyboardInterrupt:
            print("\n⚠️  Device listing interrupted.\n")
            log.warning("Device listing interrupted by user")

    def connect_to_device(self) -> None:
        """Connect to a selected device and open its menu."""
        log.info("Selected: Connect to a Device")
        try:
            connect_to_device.connect_to_device()
        except KeyboardInterrupt:
            print("\n⚠️  Device connection interrupted. Returning to main menu.\n")
            log.warning("Device connection interrupted by user")
        except Exception as e:  # pragma: no cover - defensive
            error_utils.show_error(f"Failed to connect to device: {e}")

    def open_database_menu(self) -> None:
        """Open the interactive database menu."""
        log.info("Opened Database Menu")
        DatabaseMenu().show()

    def run_test_suite(self) -> None:
        """Execute the full pytest suite and show results."""
        log.info("Selected: Run Test Suite")
        print("\n🧪 Running test suite...\n")
        PytestRunner().run_and_report()


# ----- Convenience wrappers -----
def show_main_menu() -> None:
    """Render the main menu."""
    MainMenu().show()


def action_run_tests() -> None:
    """Maintain backward compatibility for test runner."""
    MainMenu().run_test_suite()


def action_database_menu() -> None:
    """Backward-compatible helper to open the database menu."""
    MainMenu().open_database_menu()


def action_show_connected_devices() -> None:
    """Backward-compatible helper to list connected devices."""
    MainMenu().show_connected_devices()


def action_connect_to_device() -> None:
    """Backward-compatible helper to connect to a device."""
    MainMenu().connect_to_device()


__all__ = [
    "MainMenu",
    "show_main_menu",
    "action_run_tests",
    "action_database_menu",
    "action_show_connected_devices",
    "action_connect_to_device",
]
