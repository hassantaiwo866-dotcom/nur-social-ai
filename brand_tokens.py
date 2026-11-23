"""Canonical Nūr Media visual identity tokens.

Keep source footage natural; brand colours belong in graphic elements and overlays.
"""
from __future__ import annotations

PALETTE_HEX = {
    "primary_emerald": "#0B5D3B",
    "deep_forest": "#064E3B",
    "near_black": "#080808",
    "warm_ivory": "#F5F0E1",
    "muted_gold": "#D4AF37",
    "earth_bronze": "#A68A64",
    "charcoal": "#1C1C1C",
}

def rgb(name: str) -> tuple[int, int, int]:
    """Return a palette colour as an RGB tuple."""
    value = PALETTE_HEX[name].lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))

PRIMARY_EMERALD = rgb("primary_emerald")
DEEP_FOREST = rgb("deep_forest")
NEAR_BLACK = rgb("near_black")
WARM_IVORY = rgb("warm_ivory")
MUTED_GOLD = rgb("muted_gold")
EARTH_BRONZE = rgb("earth_bronze")
CHARCOAL = rgb("charcoal")

WORDMARK = "Nūr"
TAGLINE = "Build the person you want to become."
