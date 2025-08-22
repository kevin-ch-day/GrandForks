"""Minimal interactive database menu for testing connection."""

from __future__ import annotations

from database.db_core import DatabaseCore
from database.db_engine import DbEngine
from utils.display_utils import menu_utils, error_utils


def _test_connection() -> None:
    """Attempt to connect to the database and report status."""
    core = DatabaseCore.from_config()
    engine = DbEngine(core)
    try:
        engine.init()
        if engine.is_ready():
            print("✅ Database connection successful.")
        else:  # pragma: no cover - defensive branch
            print("❌ Database connection failed.")
    except Exception as exc:  # pragma: no cover - depends on database
        error_utils.show_error(f"Connection failed: {exc}")
    finally:
        try:
            engine.shutdown()
        except Exception:  # pragma: no cover - defensive shutdown
            pass


def db_menu() -> None:
    """Display a simple menu for database utilities."""
    options = {
        "1": ("Test Connection", _test_connection),
    }
    menu_utils.show_menu("Database Menu", options, exit_label="Back")


__all__ = ["db_menu"]
