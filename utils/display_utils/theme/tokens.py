"""Semantic token definitions mapping to palette keys and style attributes."""

from __future__ import annotations

from typing import Dict, Any

TokenDef = Dict[str, Any]

TOKENS: Dict[str, TokenDef] = {
    "fg.default": {"fg": "fg_default"},
    "fg.muted": {"fg": "fg_muted"},
    "fg.emphasis": {"fg": "fg_emphasis", "bold": True},
    "fg.success": {"fg": "fg_success"},
    "fg.warning": {"fg": "fg_warning"},
    "fg.error": {"fg": "fg_error"},
    "fg.info": {"fg": "fg_info"},
    "fg.accent": {"fg": "fg_accent"},
    "fg.link": {"fg": "fg_link", "underline": True},
    "bg.panel": {"bg": "bg_panel"},
    "bg.bar": {"bg": "bg_bar"},
    "border.dim": {"fg": "border_dim"},
    "border.strong": {"fg": "border_strong", "bold": True},
    "badge.low": {"fg": "fg_emphasis", "bg": "badge_low", "bold": True},
    "badge.med": {"fg": "fg_emphasis", "bg": "badge_med", "bold": True},
    "badge.high": {"fg": "fg_emphasis", "bg": "badge_high", "bold": True},
    "bold": {"bold": True},
    "underline": {"underline": True},
}
