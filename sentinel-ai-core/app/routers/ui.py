import json
import re
from pathlib import Path

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.branding import brand_css, load_brand

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


@router.get("/ui/brand.json")
def get_brand(request: Request) -> JSONResponse:
    brand = request.app.state.brand
    return JSONResponse({"name": brand.name, "accent": brand.accent, "customized": brand.customized})


@router.get("/ui/brand.css")
def get_brand_css(request: Request) -> Response:
    return Response(brand_css(request.app.state.brand), media_type="text/css")


class RevalidatedFiles(StaticFiles):
    """Static files that the browser must revalidate on every load.

    Without this a browser keeps an old app.js or styles.css next to a new
    index.html, and the page mixes two versions. The ETag keeps it cheap.
    """

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


def mount_ui(app) -> None:
    app.state.brand = load_brand()
    app.include_router(router)
    if BRANDING_DIR.is_dir():
        app.mount("/branding", RevalidatedFiles(directory=str(BRANDING_DIR)), name="branding")
    app.mount("/ui", RevalidatedFiles(directory=str(STATIC_DIR), html=True), name="ui")
