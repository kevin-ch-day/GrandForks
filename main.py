# main.py
import sys
import signal
import argparse
import logging

from config import app_config
from utils.display_utils import menu_utils, error_utils, theme
import utils.logging_utils.logging_engine as log
from device import show_devices, connect_to_device
from utils.about_app import about_app


# ---------- Menu Actions ----------

def action_show_connected_devices():
    """Action: List all connected Android devices."""
    log.info("Selected: Show Connected Devices")
    try:
        show_devices.display_detailed_devices()
    except KeyboardInterrupt:
        print("\n⚠️  Device listing interrupted.\n")
        log.warning("Device listing interrupted by user")


def action_connect_to_device():
    """Action: Connect to a selected device and open interactive menu."""
    log.info("Selected: Connect to a Device")
    try:
        connect_to_device.connect_to_device()
    except KeyboardInterrupt:
        print("\n⚠️  Device connection interrupted. Returning to main menu.\n")
        log.warning("Device connection interrupted by user")
    except Exception as e:
        error_utils.show_error(f"Failed to connect to device: {e}")


def action_database_menu():
    """Action: Database menu placeholder."""
    log.info("Opened Database Menu")
    # TODO: Hook into actual DB logic once implemented
    print("\n[TODO] Database Menu\n")


# ---------- Signal Handling ----------

def handle_interrupt(sig, frame):
    """Gracefully handle Ctrl+C interrupts."""
    print("\n\n⚠️  Interrupted by user.")
    log.warning("Application interrupted with Ctrl+C")
    # Raise to let outer try/except handle clean exit messaging
    raise KeyboardInterrupt


# ---------- Main Entry ----------

def main():
    """Main entry point for the Android Tool CLI."""
    parser = argparse.ArgumentParser(description="Android Tool CLI")
    parser.add_argument(
        "--theme",
        choices=theme.available_palettes(),
        help="Color theme to use (overrides config default)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging to console",
    )
    args = parser.parse_args()

    # Apply theme from flag or config default
    selected_palette = args.theme or getattr(app_config, "THEME_PALETTE", None)
    if selected_palette:
        try:
            theme.set_palette(selected_palette)
            log.info(f"Using theme palette: {selected_palette}")
        except Exception as e:
            log.warning(f"Failed to set theme '{selected_palette}': {e}")

    # Optional verbose console logging (only if supported by logging engine)
    if args.verbose:
        if hasattr(log, "set_console_level"):
            try:
                log.set_console_level(logging.DEBUG)
            except Exception:
                # Fallback if API expects int or different signature
                try:
                    log.set_console_level("DEBUG")  # type: ignore[arg-type]
                except Exception:
                    pass
        log.info("Verbose console logging enabled")

    # Trap Ctrl+C
    signal.signal(signal.SIGINT, handle_interrupt)

    # Define main menu
    options = {
        "1": ("Show Connected Devices", action_show_connected_devices),
        "2": ("Connect to a Device", action_connect_to_device),
        "3": ("Database", action_database_menu),
        "4": ("About App", about_app),
    }

    try:
        menu_utils.show_menu(
            title=f"{app_config.APP_NAME} v{app_config.APP_VERSION}",
            options=options,
            exit_label="Exit",
        )
    except KeyboardInterrupt:
        print("\n⚠️  Main menu interrupted. Exiting.\n")
        log.warning("Main menu interrupted by user")

    log.info("Application exited cleanly")


if __name__ == "__main__":
    main()
