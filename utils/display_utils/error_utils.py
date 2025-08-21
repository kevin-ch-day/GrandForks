# utils/output_utils/error_utils.py

import sys
import traceback
from typing import Optional


def _print_block(title: str, icon: str, message: str) -> None:
    """Internal helper to render a styled message block."""
    print(f"\n{icon} {title}")
    print("-" * (len(title) + 4))
    print(message)
    print("-" * (len(title) + 4) + "\n")


def show_error(message: str, exit_app: bool = False, exit_code: int = 1, exc: Optional[Exception] = None) -> None:
    """
    Display a formatted error message. Optionally exit the application.

    Args:
        message (str): The error message to display.
        exit_app (bool): If True, exits the application.
        exit_code (int): Exit code when terminating (default 1).
        exc (Exception): Optional exception to include traceback for debugging.
    """
    _print_block("ERROR", "❌", message)

    if exc:
        print("🔎 Debug Traceback:")
        traceback.print_exception(type(exc), exc, exc.__traceback__)

    if exit_app:
        sys.exit(exit_code)


def show_warning(message: str) -> None:
    """Display a formatted warning message."""
    _print_block("WARNING", "⚠️", message)


def show_info(message: str) -> None:
    """Display a formatted info message."""
    _print_block("INFO", "ℹ️", message)


def handle_error(message: str, exc: Optional[Exception] = None, exit_app: bool = False) -> None:
    """
    Generic error handler that can be reused across the app.
    Shortcut for show_error.
    """
    show_error(message, exit_app=exit_app, exc=exc)


def handle_warning(message: str) -> None:
    """Generic warning handler (shortcut for show_warning)."""
    show_warning(message)


def handle_info(message: str) -> None:
    """Generic info handler (shortcut for show_info)."""
    show_info(message)
