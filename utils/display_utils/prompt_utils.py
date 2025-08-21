# utils/display_utils/prompt_utils.py

from . import theme


def ask_yes_no(question: str, default: str = "y") -> bool:
    """Ask a yes/no question and return True/False with themed feedback."""

    if default.lower() == "y":
        choices = f" [{theme.style('fg.accent', 'bold')('Y')}/{theme.style('fg.muted')('n')}] "
    else:
        choices = f" [{theme.style('fg.muted')('y')}/{theme.style('fg.accent', 'bold')('N')}] "

    prompt = f"{theme.header(question)}{choices}"

    while True:
        answer = input(prompt).strip().lower()

        if not answer:
            result = default.lower() == "y"
        elif answer in ("y", "yes"):
            result = True
        elif answer in ("n", "no"):
            result = False
        else:
            print(theme.style("fg.warning")("Invalid input. Please enter y or n."))
            continue

        if result:
            print(theme.style("fg.success", "bold")("Yes"))
        else:
            print(theme.style("fg.error", "bold")("No"))

        return result
