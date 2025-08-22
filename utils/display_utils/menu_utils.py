# utils/display_utils/menu_utils.py

import sys
from typing import Callable, Dict, Tuple, List, Optional
from utils.display_utils import prompt_utils, error_utils, theme
import utils.logging_utils.logging_engine as log

INVERSE = "\x1b[7m"
RESET = "\x1b[0m"


class MenuExit(Exception):
    """Signal that the current menu should exit early."""
    pass


# ---------- Rendering Helpers ----------

def print_menu_header(title: str) -> None:
    """Render a styled header for the menu."""
    print("\n" + theme.hr("bar"))
    print(theme.header(title))
    print(theme.hr("bar"))


def print_menu_options(
    options: Dict[str, Tuple[str, Callable]],
    exit_label: str,
    highlight: Optional[str] = None,
    highlight_style: str = "inverse",
) -> None:
    """Render all menu options in sorted order.

    Args:
        options: Mapping of option keys to (label, callable). Keys are strings
            such as "1", "A", etc. Keys comprised solely of digits are sorted
            numerically; all other keys fall back to lexical (alphabetical)
            ordering. Mixing numeric and non-numeric keys is supported.
        exit_label: Text for the exit option.
        highlight: Option key to visually emphasize.
        highlight_style: Style token for highlighting (inverse, bold, accent).
    """
    num_style = theme.style("fg.info", "bold")
    exit_style = theme.style("fg.success", "bold")
    styles = {
        "inverse": lambda s: f"{INVERSE}{s}{RESET}",
        "bold": theme.style("bold"),
        "accent": theme.style("fg.accent", "bold"),
    }
    style_fn = styles.get(highlight_style, styles["inverse"])

    def sort_key(k: str):
        return (0, int(k)) if k.isdigit() else (1, k)

    for key in sorted(options.keys(), key=sort_key):
        label, _ = options[key]
        hot = num_style(f"[{key}]")
        if highlight == key:
            line = f"{style_fn('▶')} {hot} {style_fn(label)}"
        else:
            line = f" {hot} {label}"
        print(line)
    hot = exit_style("[0]")
    if highlight == "0":
        line = f"{style_fn('▶')} {hot} {style_fn(exit_label)}"
    else:
        line = f" {hot} {exit_label}"
    print(line)


# ---------- Input Handling ----------

def _get_choice(prompt: str = "👉 Select an option: ") -> str:
    """Read and normalize user input."""
    return input(prompt).strip()


def _validate_choice(choice: str, options: Dict[str, Tuple[str, Callable]]) -> bool:
    """Check if a menu choice is valid."""
    return choice == "0" or choice in options


# ---------- Core Menu Loop ----------

def show_menu(
    title: str,
    options: Dict[str, Tuple[str, Callable]],
    exit_label: str = "Exit",
    default_choice: Optional[str] = None,
    highlight_choice: Optional[str] = None,
    highlight_style: str = "inverse",
) -> None:
    """
    A reusable interactive menu framework for CLI tools.

    Args:
        title (str): The title displayed at the top of the menu.
        options (dict): Dict mapping string keys ("1", "2", ...) to (label, function).
        exit_label (str): Label for the exit/return option (default: "Exit").
        default_choice (str): If provided, auto-select this choice (useful for automation/tests).
        highlight_choice (str): Option key to highlight when rendering the menu.
        highlight_style (str): Style for highlighting ("inverse", "bold", or "accent").
    """
    while True:
        print_menu_header(title)
        print(theme.hr("thin"))
        print_menu_options(options, exit_label, highlight_choice or default_choice, highlight_style)
        print(theme.hr("thin"))

        choice = default_choice or _get_choice()

        if not _validate_choice(choice, options):
            error_utils.show_warning("Invalid choice. Please try again.")
            continue

        if choice == "0":
            print(f"\n🔙 Returning from '{title}'...\n")
            break

        label, action = options[choice]
        try:
            run_menu_action(label, action)
        except MenuExit:
            break


# ---------- Action Helpers ----------

def run_menu_action(label: str, action: Callable) -> None:
    """Run a menu action safely with error handling."""
    try:
        print(theme.style("fg.accent", "bold")(f"\n▶ Running: {label}\n"))
        action()
    except KeyboardInterrupt:
        print("\n⚠️  Action interrupted by user.\n")
        log.warning(f"Action '{label}' interrupted by user")
    except MenuExit:
        raise
    except Exception as e:
        error_utils.handle_error(f"Error while running '{label}': {e}", exc=e)


def confirm_and_run(label: str, action: Callable, *args, default: str = "y") -> None:
    """
    Prompt the user for confirmation before running an action.
    Uses prompt_utils.ask_yes_no for consistency.
    """
    if prompt_utils.ask_yes_no(f"Run '{label}'?", default=default):
        try:
            action(*args)
        except Exception as e:
            error_utils.handle_error(f"Error in confirmed action '{label}': {e}", exc=e)
    else:
        print(f"❌ Skipped '{label}'.")


# ---------- Utility Menus ----------

def simple_menu(title: str, items: List[str], exit_label: str = "Back") -> int:
    """
    Display a simple numbered list menu (no functions).
    Returns the selected index (1-based) or 0 if exit.
    """
    while True:
        print_menu_header(title)
        print(theme.hr("thin"))
        num_style = theme.style("fg.info", "bold")
        exit_style = theme.style("fg.success", "bold")
        for idx, item in enumerate(items, start=1):
            hot = num_style(f"[{idx}]")
            print(f" {hot} {item}")
        hot = exit_style("[0]")
        print(f" {hot} {exit_label}")
        print(theme.hr("thin"))

        choice = _get_choice()

        if choice == "0":
            return 0
        elif choice.isdigit() and 1 <= int(choice) <= len(items):
            return int(choice)
        else:
            error_utils.show_warning("Invalid choice. Please try again.")


def exit_program(confirm: bool = True) -> None:
    """Gracefully exit the program with optional confirmation."""
    if not confirm or prompt_utils.ask_yes_no("Are you sure you want to exit?", default="n"):
        print("\n👋 Exiting program. Goodbye!\n")
        sys.exit(0)
