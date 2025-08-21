# utils/display_utils/menu_utils.py

import sys
from typing import Callable, Dict, Tuple, List, Optional
from utils.display_utils import prompt_utils, error_utils

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    class _NoColor:
        RED = YELLOW = CYAN = RESET_ALL = ""
    Fore = Style = _NoColor()


# ---------- Rendering Helpers ----------

def print_menu_header(title: str) -> None:
    """Render a styled header for the menu."""
    print("\n" + "=" * 50)
    print(f"{Fore.CYAN}{title}{Style.RESET_ALL}")
    print("=" * 50)


def print_menu_options(options: Dict[str, Tuple[str, Callable]], exit_label: str) -> None:
    """Render all menu options in sorted order."""
    for key in sorted(options.keys(), key=lambda x: int(x)):
        label, _ = options[key]
        print(f" [{key}] {label}")
    print(f" [0] {exit_label}")
    print("-" * 50)


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
    default_choice: Optional[str] = None
) -> None:
    """
    A reusable interactive menu framework for CLI tools.

    Args:
        title (str): The title displayed at the top of the menu.
        options (dict): Dict mapping string keys ("1", "2", ...) to (label, function).
        exit_label (str): Label for the exit/return option (default: "Exit").
        default_choice (str): If provided, auto-select this choice (useful for automation/tests).
    """
    while True:
        print_menu_header(title)
        print_menu_options(options, exit_label)

        choice = default_choice or _get_choice()

        if not _validate_choice(choice, options):
            error_utils.show_warning("Invalid choice. Please try again.")
            continue

        if choice == "0":
            print(f"\n🔙 Returning from '{title}'...\n")
            break

        label, action = options[choice]
        run_menu_action(label, action)


# ---------- Action Helpers ----------

def run_menu_action(label: str, action: Callable) -> None:
    """Run a menu action safely with error handling."""
    try:
        print(f"\n▶ Running: {label}\n")
        action()
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
        for idx, item in enumerate(items, start=1):
            print(f" [{idx}] {item}")
        print(f" [0] {exit_label}")
        print("-" * 50)

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
