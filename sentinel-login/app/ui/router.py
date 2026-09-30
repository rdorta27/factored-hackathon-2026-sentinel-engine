"""Same-process frontend: static files, brand assets, and locale merging."""

import json
import re
from pathlib import Path

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter(tags=["ui"])

STATIC_DIR = Path(__file__).parent / "static"
I18N_DIR = Path(__file__).parent / "i18n"
# The team's branding folder is the single source of truth for color and type.
# It is read and served as-is: never copied and never modified here.
BRANDING_DIR = Path(__file__).resolve().parents[3] / "branding"
LOCALE_PATTERN = re.compile(r"^[a-z]{2}-[A-Za-z0-9]{2,3}$")
BASE_LOCALE = "es-419"


def load_locale(locale: str) -> dict | None:
    """Merge the base dictionary with regional overrides.

    Regional files (es-*) carry only changed strings and fall back to
    es-419 for everything else. Unknown locales return None.
    """
    if not LOCALE_PATTERN.match(locale):
        return None
    base_path = I18N_DIR / f"{BASE_LOCALE}.json"
    merged = json.loads(base_path.read_text(encoding="utf-8"))
    if locale == BASE_LOCALE:
        return merged
    override_path = I18N_DIR / f"{locale}.json"
    if not override_path.exists():
        return None
    merged.update(json.loads(override_path.read_text(encoding="utf-8")))
    return merged


@router.get("/i18n/{locale}")
def get_locale(locale: str) -> JSONResponse:
    strings = load_locale(locale)
    if strings is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Unknown locale"},
        )
    return JSONResponse(status_code=status.HTTP_200_OK, content=strings)


def mount_ui(app) -> None:  # type: ignore[no-untyped-def]
    """Serve the single-page frontend under /ui and the brand folder under /branding.

    Mounting at "/" would shadow every API route declared after it, and the
    page would request /ui/styles.css which only exists under this prefix.
    """
    app.include_router(router)
    if BRANDING_DIR.is_dir():
        app.mount(
            "/branding",
            StaticFiles(directory=str(BRANDING_DIR)),
            name="branding",
        )
    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")
