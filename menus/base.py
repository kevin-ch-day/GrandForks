from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from utils.display_utils import menu_utils


@dataclass
class MenuAction:
    """Represents a single menu entry and its handler."""
    label: str
    handler: Callable[[], None]


@dataclass
class BaseMenu:
    """Simple object-oriented wrapper around menu rendering."""
    title: str
    exit_label: str = "Exit"
    highlight_choice: Optional[str] = None
    highlight_style: str = "accent"
    actions: Dict[str, MenuAction] = field(default_factory=dict)

    def show(self) -> None:
        """Render the menu using ``menu_utils``."""
        options = {k: (a.label, a.handler) for k, a in self.actions.items()}
        menu_utils.show_menu(
            title=self.title,
            options=options,
            exit_label=self.exit_label,
            highlight_choice=self.highlight_choice,
            highlight_style=self.highlight_style,
        )
