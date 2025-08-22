"""Interactive database menu implemented as a class.

This module previously exposed a simple function that rendered a menu
using ``menu_utils``.  To better align with the object's oriented design of
the rest of the CLI, it now provides :class:`DatabaseMenu` which inherits
from :class:`menus.base.BaseMenu`.

The menu currently exposes a single action to test the database
connection but can easily be extended with additional options in the
future.
"""

from __future__ import annotations

from menus.base import BaseMenu, MenuAction
from database.db_core import DatabaseCore
from database.db_engine import DbEngine
from utils.display_utils import error_utils


class DatabaseMenu(BaseMenu):
    """Small menu for database related utilities."""

    def __init__(self) -> None:  # pragma: no cover - simple wiring
        super().__init__(title="Database Menu", exit_label="Back")
        self.actions = {
            "1": MenuAction("Test Connection", self.test_connection),
        }

    def test_connection(self) -> None:
        """Attempt to connect to the configured database and report status."""
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


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------
def db_menu() -> None:
    """Render the :class:`DatabaseMenu` (backwards compatible helper)."""
    DatabaseMenu().show()


__all__ = ["DatabaseMenu", "db_menu"]

