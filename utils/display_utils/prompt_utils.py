# utils/display_utils/prompt_utils.py

from . import theme


def ask_yes_no(question: str, default: str = "y") -> bool:
    """Ask a yes/no question and return True/False."""

    if default.lower() == "y":
        choices = f" [{theme.style('fg.accent', 'bold')('Y')}/{theme.style('fg.muted')('n')}] "
    else:
        choices = f" [{theme.style('fg.muted')('y')}/{theme.style('fg.accent', 'bold')('N')}] "

    while True:
        answer = input(f"{theme.header(question)}{choices}").strip().lower()

        if not answer:
            return default.lower() == "y"

        if answer in ("y", "yes"):
            return True
        elif answer in ("n", "no"):
            return False
        else:
            print(theme.style("fg.warning")("Invalid input. Please enter y or n."))
