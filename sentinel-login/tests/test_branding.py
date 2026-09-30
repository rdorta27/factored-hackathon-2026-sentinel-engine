"""Branding adoption: brand assets are served, local CSS stays layout-only.

The brand folder is the team's single source of truth for color and type. These
tests are the lock: if the local sheet grows a color or a font, or if the app
stops loading the brand sheets, the suite fails.
"""

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.ui.router import BRANDING_DIR

STATIC_DIR = Path(__file__).parent.parent / "app" / "ui" / "static"
LAYOUT_CSS = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
INDEX = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
APP_JS = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

LAYOUT_PATH = STATIC_DIR / "styles.css"


def client() -> TestClient:
    return TestClient(create_app())


# --- Brand assets are served -------------------------------------------


def test_brand_folder_exists_untouched() -> None:
    assert BRANDING_DIR.is_dir(), "branding/ must be present at the repo root"
    for name in ("brand.css", "chat.css", "theme-sentinel.css"):
        assert (BRANDING_DIR / name).is_file(), f"missing brand file: {name}"


def test_brand_sheets_are_served() -> None:
    c = client()
    for path in ("/branding/brand.css", "/branding/chat.css"):
        response = c.get(path)
        assert response.status_code == 200, path


def test_page_links_brand_sheets_before_the_local_one() -> None:
    assert 'href="/branding/brand.css"' in INDEX
    assert 'href="/branding/chat.css"' in INDEX
    assert INDEX.index("/branding/brand.css") < INDEX.index("/ui/styles.css")
    assert INDEX.index("/branding/chat.css") < INDEX.index("/ui/styles.css")


def test_local_sheet_is_served() -> None:
    assert client().get("/ui/styles.css").status_code == 200


def test_no_dead_stylesheet_is_left_behind() -> None:
    """The old private palette sheet was replaced, not kept alongside."""
    sheets = sorted(p.name for p in STATIC_DIR.glob("*.css"))
    assert sheets == ["styles.css"], f"expected one local sheet, found {sheets}"
    assert "--color-primary" not in LAYOUT_CSS
    assert "system-ui" not in LAYOUT_CSS


def test_theme_is_driven_by_data_theme() -> None:
    assert 'data-theme="light"' in INDEX
    assert "document.documentElement.dataset.theme" in APP_JS


# --- The local sheet is layout-only (the lock) -------------------------

COLOR_LITERAL = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)"
)
NAMED_COLORS = (
    "white", "black", "red", "blue", "green", "yellow", "orange", "purple",
    "gray", "grey", "pink", "silver", "navy", "teal",
)


def test_local_sheet_has_no_color_literal() -> None:
    found = COLOR_LITERAL.findall(LAYOUT_CSS)
    assert found == [], f"color literals in layout.css: {found}"


def test_local_sheet_has_no_named_colors() -> None:
    # Match a color keyword only in a value position, not in a comment.
    code = re.sub(r"/\*.*?\*/", "", LAYOUT_CSS, flags=re.DOTALL)
    offenders = [
        word
        for word in NAMED_COLORS
        if re.search(rf":\s*[^;]*\b{word}\b", code, flags=re.IGNORECASE)
    ]
    assert offenders == [], f"named colors in layout.css: {offenders}"


def test_local_sheet_declares_no_font_size_or_weight() -> None:
    code = re.sub(r"/\*.*?\*/", "", LAYOUT_CSS, flags=re.DOTALL)
    for prop in ("font-size", "font-weight"):
        assert prop not in code, f"layout.css must not declare {prop}"


def test_local_sheet_uses_mono_only_through_a_brand_variable() -> None:
    """The one typography rule allowed is a single brand variable reference."""
    code = re.sub(r"/\*.*?\*/", "", LAYOUT_CSS, flags=re.DOTALL)
    found = re.findall(r"font-family\s*:\s*([^;]+);", code)
    assert found == ["var(--font-mono)"], (
        f"exactly one font rule, from a brand variable; got: {found}"
    )


def test_local_sheet_only_colors_through_brand_variables() -> None:
    """No color-valued declaration may carry anything but a var() or a keyword."""
    code = re.sub(r"/\*.*?\*/", "", LAYOUT_CSS, flags=re.DOTALL)
    color_props = (
        "color", "background-color", "border-color", "border-top-color",
        "border-right-color", "border-bottom-color", "border-left-color",
        "outline-color", "box-shadow", "fill", "stroke",
    )
    allowed_keywords = ("none", "transparent", "inherit", "currentcolor")
    for prop, value in re.findall(r"([a-z-]+)\s*:\s*([^;]+);", code):
        if prop not in color_props:
            continue
        stripped = value.strip().lower()
        assert stripped.startswith("var(") or stripped in allowed_keywords, (
            f"{prop}: {value} is not a brand variable"
        )


def test_verified_color_is_configurable_in_one_place() -> None:
    code = re.sub(r"/\*.*?\*/", "", LAYOUT_CSS, flags=re.DOTALL)
    assert "--app-verified: var(--ok)" in code
    # Declared once, then referenced once by the only rule that paints it.
    assert code.count("--app-verified") == 2


# --- Functional contracts survive -------------------------------------

def test_real_app_ids_still_present() -> None:
    c = client()
    page = c.get("/ui/")
    assert page.status_code == 200
    for real_id in ('id="view-login"', 'id="thread"', 'id="transactions"'):
        assert real_id in page.text, f"app markup missing {real_id}"


def test_api_routes_survive_the_brand_mount() -> None:
    c = client()
    assert c.get("/i18n/es-419").status_code == 200
    assert c.get("/docs").status_code == 200
    assert c.post("/auth/login", json={}).status_code == 422


def test_no_inline_style_attributes_in_markup() -> None:
    assert "style=" not in INDEX, "markup must not carry inline styles"
