"""White label: the bank name and the accent color come from the environment.

``SENTINEL_BRAND_NAME`` and ``SENTINEL_BRAND_ACCENT`` replace the defaults.
An accent that fails the contrast check falls back to the default and the
fallback is logged. The check is the one of ``chat-ui``: white text on the
accent fill, and the accent as text on the card surfaces, at least 4.5:1.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_NAME = "Sentinel"
DEFAULT_ACCENT = "#1f4fa3"
MIN_CONTRAST = 4.5
MAX_NAME = 40

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
# The card surfaces of branding/brand.css, light and dark.
_LIGHT_SURFACE = "#ffffff"
_DARK_SURFACE = "#162033"


@dataclass(frozen=True)
class Brand:
    name: str
    accent: str
    accent_text_dark: str
    customized: bool


def _luminance(color: str) -> float:
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground: str, background: str) -> float:
    high, low = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _lighten(color: str, amount: float) -> str:
    channels = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(c + (255 - c) * amount):02x}" for c in channels)


def _mix(color: str, other: str, amount: float) -> str:
    """``amount`` of ``other`` mixed into ``color``."""
    a = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * amount):02x}" for x, y in zip(a, b))


def _text_on(fill: str, color: str, toward: str) -> str:
    """The color, moved toward ``toward`` until it reads on ``fill`` at 4.5:1."""
    for step in range(0, 11):
        candidate = _mix(color, toward, step / 10)
        if contrast(candidate, fill) >= MIN_CONTRAST:
            return candidate
    return toward


def tints(accent: str) -> dict[str, dict[str, str]]:
    """Soft fills and their text for the pills and callouts, in both themes."""
    light_fill = _mix(accent, "#ffffff", 0.9)
    light_row = _mix(accent, "#ffffff", 0.95)
    dark_fill = _mix(accent, _DARK_SURFACE, 0.78)
    dark_row = _mix(accent, _DARK_SURFACE, 0.9)
    return {
        "light": {"fill": light_fill, "row": light_row, "text": _text_on(light_fill, accent, "#000000")},
        "dark": {"fill": dark_fill, "row": dark_row, "text": _text_on(dark_fill, _dark_text_variant(accent), "#ffffff")},
    }


def _dark_text_variant(accent: str) -> str:
    """The lightest step of the accent that reads on the dark card surface."""
    for step in range(0, 11):
        candidate = _lighten(accent, step / 10)
        if contrast(candidate, _DARK_SURFACE) >= MIN_CONTRAST:
            return candidate
    return "#ffffff"


def accent_passes(accent: str) -> bool:
    """White on the accent fill, and the accent as text on a light card."""
    return contrast("#ffffff", accent) >= MIN_CONTRAST and contrast(accent, _LIGHT_SURFACE) >= MIN_CONTRAST


def load_brand() -> Brand:
    raw_name = os.environ.get("SENTINEL_BRAND_NAME", "").strip()
    name = " ".join(raw_name.split())[:MAX_NAME] or DEFAULT_NAME
    raw_accent = os.environ.get("SENTINEL_BRAND_ACCENT", "").strip()
    accent = DEFAULT_ACCENT
    if raw_accent:
        if not _HEX.match(raw_accent):
            logger.warning("SENTINEL_BRAND_ACCENT is not a #rrggbb color; using the default accent")
        elif not accent_passes(raw_accent.lower()):
            logger.warning(
                "SENTINEL_BRAND_ACCENT %s fails the %.1f:1 contrast check; using the default accent",
                raw_accent,
                MIN_CONTRAST,
            )
        else:
            accent = raw_accent.lower()
    return Brand(
        name=name,
        accent=accent,
        accent_text_dark=_dark_text_variant(accent),
        customized=name != DEFAULT_NAME or accent != DEFAULT_ACCENT,
    )


def brand_css(brand: Brand) -> str:
    """CSS that overrides the accent tokens. Empty when the brand is the default."""
    if brand.accent == DEFAULT_ACCENT:
        return "/* default accent */\n"
    tone = tints(brand.accent)
    light, dark = tone["light"], tone["dark"]
    return (
        f":root {{ --accent: {brand.accent}; --accent-text: {brand.accent};"
        f" --pill-info-bg: {light['fill']}; --pill-info-text: {light['text']};"
        f" --callout-bg: {light['fill']}; --th-bg: {light['fill']}; --row-alt: {light['row']};"
        f" --th-text: {light['text']}; }}\n"
        f'[data-theme="dark"] {{ --accent: {brand.accent}; --accent-text: {brand.accent_text_dark};'
        f" --pill-info-bg: {dark['fill']}; --pill-info-text: {dark['text']};"
        f" --callout-bg: {dark['fill']}; --th-bg: {dark['fill']}; --row-alt: {dark['row']};"
        f" --th-text: {dark['text']}; }}\n"
    )
