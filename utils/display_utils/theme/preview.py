"""CLI preview for theme tokens and helpers."""

from __future__ import annotations

import argparse

from . import api as theme
from . import tokens
from . import palettes


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview theme tokens")
    parser.add_argument("--theme", choices=list(palettes.PALETTES.keys()), default=theme.get_palette())
    args = parser.parse_args()

    theme.set_palette(args.theme)

    print(f"Palette: {args.theme}\n")
    for name in sorted(tokens.TOKENS.keys()):
        styled = theme.style(name)(name)
        print(f"{name:15} {styled}")
    print()
    for lvl in ("low", "med", "high"):
        print(theme.badge(lvl.upper(), lvl))


if __name__ == "__main__":
    main()
