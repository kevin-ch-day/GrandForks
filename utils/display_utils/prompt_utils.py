# utils/display_utils/prompt_utils.py

def ask_yes_no(question: str, default: str = "y") -> bool:
    # Ask a yes/no question and return True/False
    # default can be "y" or "n"

    choices = " [Y/n] " if default.lower() == "y" else " [y/N] "

    while True:
        answer = input(f"{question}{choices}").strip().lower()

        if not answer:
            return default.lower() == "y"

        if answer in ("y", "yes"):
            return True
        elif answer in ("n", "no"):
            return False
        else:
            print("Invalid input. Please enter y or n.")
