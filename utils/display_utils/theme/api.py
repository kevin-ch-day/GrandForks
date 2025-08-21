"""Public theming API used throughout the application."""

from __future__ import annotations

import os
import sys
from typing import Callable, List

from . import palettes, tokens

RESET = "\x1b[0m"

_current_palette_name = os.getenv("GF_THEME")
if not _current_palette_name:
    try:
        from config import app_config

        _current_palette_name = getattr(app_config, "THEME_PALETTE", "cyber")
    except Exception:  # pragma: no cover - config missing during tests
        _current_palette_name = "cyber"

_current_palette = palettes.PALETTES.get(_current_palette_name, palettes.PALETTES["cyber"])


def set_palette(name: str) -> None:
    """Switch to a new palette by name."""
    global _current_palette_name, _current_palette
    if name in palettes.PALETTES:
        _current_palette_name = name
        _current_palette = palettes.PALETTES[name]


def get_palette() -> str:
    return _current_palette_name


def available_palettes() -> List[str]:
    return list(palettes.PALETTES.keys())


def _supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    if not sys.stdout.isatty() and not os.getenv("FORCE_COLOR"):
        return False
    return True


def _color_mode() -> str:
    if not _supports_color():
        return "none"
    if os.getenv("FORCE_COLOR"):
        return "truecolor"
    colorterm = os.getenv("COLORTERM", "")
    if "truecolor" in colorterm or "24bit" in colorterm:
        return "truecolor"
    term = os.getenv("TERM", "")
    if "256color" in term:
        return "256"
    return "16"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _code_for(color_key: str, mode: str, is_bg: bool) -> str:
    info = _current_palette[color_key]
    if mode == "truecolor":
        r, g, b = _hex_to_rgb(info["truecolor"])
        prefix = 48 if is_bg else 38
        return f"\x1b[{prefix};2;{r};{g};{b}m"
    if mode == "256":
        prefix = 48 if is_bg else 38
        return f"\x1b[{prefix};5;{info['256']}m"
    if mode == "16":
        base = info["16"]
        code = base + 10 if is_bg else base
        return f"\x1b[{code}m"
    return ""


def color(token: str) -> str:
    """Return ANSI start sequence for a semantic token."""
    mode = _color_mode()
    token_def = tokens.TOKENS.get(token)
    if not token_def or mode == "none":
        return ""
    parts: List[str] = []
    fg_key = token_def.get("fg")
    bg_key = token_def.get("bg")
    if fg_key:
        parts.append(_code_for(fg_key, mode, False))
    if bg_key:
        parts.append(_code_for(bg_key, mode, True))
    if token_def.get("bold"):
        parts.append("\x1b[1m")
    if token_def.get("underline"):
        parts.append("\x1b[4m")
    return "".join(parts)


def style(*token_names: str) -> Callable[[str], str]:
    """Compose multiple tokens into a callable that styles text."""
    start = "".join(color(t) for t in token_names)

    def apply(text: str) -> str:
        return f"{start}{text}{RESET}"

    return apply


def header(text: str) -> str:
    return style("fg.emphasis")(text)


def badge(text: str, level: str = "med") -> str:
    token = f"badge.{level}"
    return style(token)(f"[{text}]")


def kv(key: str, val: str, level: str = "info") -> str:
    key_s = style("fg.emphasis", "bold")(key)
    val_s = style(f"fg.{level}")(val)
    return f"{key_s}: {val_s}"


def hr(kind: str = "bar", width: int = 50) -> str:
    char = "─" if kind == "bar" else ("-" if kind == "thin" else "- ")
    line = (char * width) if kind != "dashed" else ("- " * (width // 2))
    token = "border.strong" if kind == "bar" else "border.dim"
    return style(token)(line)


def progress(n: int, total: int, width: int = 40) -> str:
    if total <= 0:
        pct = 0
    else:
        pct = max(0.0, min(1.0, n / total))
    filled = int(width * pct)
    bar = "#" * filled + "-" * (width - filled)
    return style("fg.accent", "bold")(f"[{bar}] {n}/{total}")
