import json
import re
from pathlib import Path

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter(tags=["ui"])

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
I18N_DIR = STATIC_DIR / "i18n"
BRANDING_DIR = Path(__file__).resolve().parents[3] / "branding"
LOCALE_PATTERN = re.compile(r"^[a-z]{2}-[A-Za-z0-9]{2,3}$")
BASE_LOCALE = "es-419"


def load_locale(locale: str) -> dict | None:
    if not LOCALE_PATTERN.match(locale):
        return None
    base_path = I18N_DIR / f"{BASE_LOCALE}.json"
    if not base_path.is_file():
        return None
    merged = json.loads(base_path.read_text(encoding="utf-8"))
    if locale == BASE_LOCALE:
        return merged
    override = I18N_DIR / f"{locale}.json"
    if not override.is_file():
        return None
    if locale == "pt-BR":
        return json.loads(override.read_text(encoding="utf-8"))
    merged.update(json.loads(override.read_text(encoding="utf-8")))
    return merged


@router.get("/i18n/{locale}")
def get_locale(locale: str) -> JSONResponse:
    strings = load_locale(locale)
    if strings is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Unknown locale"})
    return JSONResponse(status_code=status.HTTP_200_OK, content=strings)


def mount_ui(app) -> None:
    app.include_router(router)
    if BRANDING_DIR.is_dir():
        app.mount("/branding", StaticFiles(directory=str(BRANDING_DIR)), name="branding")
    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR), html=True), name="ui")
