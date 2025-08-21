"""Color palette definitions with multiple fallbacks."""

from __future__ import annotations

from typing import Dict

# Each palette maps a color key to dictionaries specifying color codes for
# truecolor (hex string), 256-color (int) and 16-color (ANSI code for foreground).

Palette = Dict[str, Dict[str, object]]

PALETTES: Dict[str, Palette] = {
    "cyber": {
        "fg_default": {"truecolor": "#C0C0C0", "256": 250, "16": 37},
        "fg_muted": {"truecolor": "#808080", "256": 244, "16": 90},
        "fg_emphasis": {"truecolor": "#FFFFFF", "256": 15, "16": 97},
        "fg_success": {"truecolor": "#00FF88", "256": 48, "16": 32},
        "fg_warning": {"truecolor": "#FFCC00", "256": 220, "16": 33},
        "fg_error": {"truecolor": "#FF0066", "256": 197, "16": 31},
        "fg_info": {"truecolor": "#33CCFF", "256": 39, "16": 36},
        "fg_accent": {"truecolor": "#FF00FF", "256": 201, "16": 35},
        "fg_link": {"truecolor": "#00AAFF", "256": 39, "16": 34},
        "bg_panel": {"truecolor": "#111111", "256": 233, "16": 30},
        "bg_bar": {"truecolor": "#222222", "256": 235, "16": 30},
        "border_dim": {"truecolor": "#333333", "256": 236, "16": 90},
        "border_strong": {"truecolor": "#00FFFF", "256": 51, "16": 36},
        "badge_low": {"truecolor": "#0066FF", "256": 27, "16": 34},
        "badge_med": {"truecolor": "#FF8800", "256": 208, "16": 33},
        "badge_high": {"truecolor": "#FF0055", "256": 197, "16": 31},
    },
    "stealth": {
        "fg_default": {"truecolor": "#C0C0C0", "256": 250, "16": 37},
        "fg_muted": {"truecolor": "#666666", "256": 242, "16": 90},
        "fg_emphasis": {"truecolor": "#FFFFFF", "256": 15, "16": 97},
        "fg_success": {"truecolor": "#8FBC8F", "256": 108, "16": 32},
        "fg_warning": {"truecolor": "#B0B000", "256": 142, "16": 33},
        "fg_error": {"truecolor": "#B22222", "256": 124, "16": 31},
        "fg_info": {"truecolor": "#708090", "256": 103, "16": 36},
        "fg_accent": {"truecolor": "#4682B4", "256": 67, "16": 34},
        "fg_link": {"truecolor": "#87CEFA", "256": 117, "16": 34},
        "bg_panel": {"truecolor": "#0A0A0A", "256": 232, "16": 30},
        "bg_bar": {"truecolor": "#1A1A1A", "256": 234, "16": 30},
        "border_dim": {"truecolor": "#2A2A2A", "256": 235, "16": 90},
        "border_strong": {"truecolor": "#444444", "256": 238, "16": 37},
        "badge_low": {"truecolor": "#555555", "256": 240, "16": 90},
        "badge_med": {"truecolor": "#777777", "256": 243, "16": 37},
        "badge_high": {"truecolor": "#999999", "256": 246, "16": 37},
    },
    "debug": {
        "fg_default": {"truecolor": "#FFFFFF", "256": 15, "16": 97},
        "fg_muted": {"truecolor": "#AAAAAA", "256": 248, "16": 37},
        "fg_emphasis": {"truecolor": "#FFFFFF", "256": 15, "16": 97},
        "fg_success": {"truecolor": "#00FF00", "256": 46, "16": 32},
        "fg_warning": {"truecolor": "#FFFF00", "256": 226, "16": 33},
        "fg_error": {"truecolor": "#FF0000", "256": 196, "16": 31},
        "fg_info": {"truecolor": "#0000FF", "256": 21, "16": 34},
        "fg_accent": {"truecolor": "#FF00FF", "256": 201, "16": 35},
        "fg_link": {"truecolor": "#00FFFF", "256": 51, "16": 36},
        "bg_panel": {"truecolor": "#000000", "256": 16, "16": 30},
        "bg_bar": {"truecolor": "#000000", "256": 16, "16": 30},
        "border_dim": {"truecolor": "#FFFFFF", "256": 15, "16": 37},
        "border_strong": {"truecolor": "#FFFFFF", "256": 15, "16": 97},
        "badge_low": {"truecolor": "#0000FF", "256": 21, "16": 34},
        "badge_med": {"truecolor": "#FFFF00", "256": 226, "16": 33},
        "badge_high": {"truecolor": "#FF0000", "256": 196, "16": 31},
    },
}


def available_palettes() -> Dict[str, Palette]:
    """Return all available palette definitions."""
    return PALETTES
