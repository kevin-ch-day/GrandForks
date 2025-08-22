# main.py
import signal
import argparse
import logging

from config import app_config
from utils.display_utils import theme
import utils.logging_utils.logging_engine as log

from main_menu import MainMenu


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
        "--debug",
        dest="verbose",
        action="store_true",
        help="Enable debug logging to console",
    )
    parser.add_argument(
        "--artifacts",
        default="3",
        help="Number of artifacts per package to display, or 'all'",
    )
    parser.add_argument(
        "--no-artifacts",
        action="store_true",
        help="Suppress artifact display in analysis output",
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

    # Optional debug console logging (only if supported by logging engine)
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
        log.info("Debug console logging enabled")

    # Configure artifact display limit
    artifact_arg = getattr(args, "artifacts", "3")
    if args.no_artifacts:
        limit: int | None = 0
    else:
        limit = None if str(artifact_arg).lower() == "all" else int(artifact_arg)
    setattr(app_config, "ARTIFACT_LIMIT", limit)

    # Trap Ctrl+C
    signal.signal(signal.SIGINT, handle_interrupt)

    try:
        MainMenu().show()
    except KeyboardInterrupt:
        print("\n⚠️  Main menu interrupted. Exiting.\n")
        log.warning("Main menu interrupted by user")

    log.info("Application exited cleanly")


if __name__ == "__main__":
    main()
