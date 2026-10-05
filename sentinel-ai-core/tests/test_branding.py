"""Brand identity: local fonts, success token, product mark (change ui-product 1.1)."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BRANDING = REPO / "branding"
BRAND_CSS = (BRANDING / "brand.css").read_text(encoding="utf-8")
CHAT_CSS = (BRANDING / "chat.css").read_text(encoding="utf-8")
STATIC = Path(__file__).parent.parent / "app" / "static"
INDEX = (STATIC / "index.html").read_text(encoding="utf-8")
STYLES = (STATIC / "styles.css").read_text(encoding="utf-8")


def _var(block: str, name: str) -> str | None:
    match = re.search(rf"{re.escape(name)}\s*:\s*([^;]+);", block)
    return match.group(1).strip() if match else None


def test_no_external_font_or_asset_url() -> None:
    for name, css in (("brand.css", BRAND_CSS), ("chat.css", CHAT_CSS)):
        assert "fonts.googleapis.com" not in css, f"{name} requests an external font"
        assert "fonts.gstatic.com" not in css, f"{name} requests an external font"
        assert "http:// " not in css and "https://" not in css, f"{name} has an external URL"


def test_fonts_are_local_woff2_with_font_face() -> None:
    assert "@font-face" in BRAND_CSS
    for family in ("Newsreader", "Source Sans 3", "Source Code Pro"):
        assert family in BRAND_CSS, f"{family} missing from brand.css"
    fonts = BRANDING / "fonts"
    woff2 = sorted(fonts.glob("*.woff2"))
    assert len(woff2) >= 3, "branding/fonts must ship the three woff2 families"
    for path in woff2:
        assert path.stat().st_size > 1000, f"{path.name} looks empty"


def test_success_token_exists_and_differs_from_accent() -> None:
    light = BRAND_CSS.split('[data-theme="dark"] {')[0]
    dark = BRAND_CSS.split('[data-theme="dark"] {')[1]
    for theme in (light, dark):
        accent = _var(theme, "--accent")
        success = _var(theme, "--success") or _var(theme, "--ok")
        assert accent and success, "accent and success tokens must exist in both themes"
        assert success.lower() != accent.lower(), "success must be distinct from the accent"


def test_mark_is_inline_svg_with_purpose_line() -> None:
    assert "<svg" in INDEX and "</svg>" in INDEX, "the product mark must be inline SVG"
    assert 'data-testid="brand-mark"' in INDEX
    assert ">SE<" not in INDEX, "the generic SE badge is gone"
    assert 'data-i18n="purposeLine"' in INDEX


def test_app_styles_carry_layout_only() -> None:
    code = re.sub(r"/\*.*?\*/", "", STYLES, flags=re.S)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", code), "styles.css must not contain hex colors"
    assert "rgb(" not in code and "hsl(" not in code, "styles.css must not contain color functions"
    assert "font-size" not in code and "font-weight" not in code, "type lives in branding/"
    for match in re.finditer(r"font-family\s*:\s*([^;]+);", code):
        assert "var(--font-mono)" in match.group(1), "only the brand mono variable may be referenced"


def _luminance(color: str) -> float:
    digits = color.lstrip("#")
    channels = [int(digits[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(foreground: str, background: str) -> float:
    high, low = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _themes() -> dict[str, str]:
    light, dark = BRAND_CSS.split('[data-theme="dark"] {')
    return {"light": light, "dark": dark.split("@media")[0]}


def test_accent_is_the_bank_blue_in_both_themes() -> None:
    themes = _themes()
    assert _var(themes["light"], "--accent") == "#1f4fa3"
    assert _var(themes["dark"], "--accent") != _var(themes["light"], "--accent")


def test_accent_passes_aa_in_both_themes() -> None:
    # White text sits on the accent fill (buttons, user bubbles).
    # The accent text token sits on the page and card surfaces.
    for name, theme in _themes().items():
        accent = _var(theme, "--accent")
        accent_text = _var(theme, "--accent-text")
        assert _contrast("#ffffff", accent) >= 4.5, f"white on the {name} accent"
        for surface in ("--bg", "--bg-elev"):
            assert _contrast(accent_text, _var(theme, surface)) >= 4.5, f"{name} accent text on {surface}"
        for token in ("--text", "--muted"):
            assert _contrast(_var(theme, token), _var(theme, "--bg-elev")) >= 4.5, f"{name} {token}"


def test_sentinel_violet_and_rose_stay_in_the_mark_only() -> None:
    for theme in _themes().values():
        assert _var(theme, "--sentinel-violet") and _var(theme, "--sentinel-rose")
        assert _var(theme, "--accent").lower() not in {
            _var(theme, "--sentinel-violet").lower(),
            _var(theme, "--sentinel-rose").lower(),
        }
    uses = [line for line in CHAT_CSS.splitlines() if "--sentinel-" in line]
    assert len(uses) == 1 and "linear-gradient" in uses[0], "only the product mark uses the Sentinel colors"


def test_status_pills_pass_aa_in_both_themes() -> None:
    for name, theme in _themes().items():
        for pill in ("ok", "warn", "info", "neutral", "bad"):
            fill = _var(theme, f"--pill-{pill}-bg")
            text = _var(theme, f"--pill-{pill}-text")
            assert _contrast(text, fill) >= 4.5, f"{name} pill {pill}"
        assert _contrast(_var(theme, "--demo-text"), _var(theme, "--demo-bg")) >= 4.5, f"{name} demo chip"
