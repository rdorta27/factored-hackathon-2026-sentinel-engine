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
