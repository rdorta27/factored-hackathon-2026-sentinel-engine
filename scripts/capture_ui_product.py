#!/usr/bin/env python3
"""Capture the ui-product screens for the deliverable.

Screens in es-MX and pt-BR, at desktop and phone width, against an app in
demo mode: the entry, the chat after a case opens (three columns, charge
states), the chat after a handoff (handoff card), the advisor list and the
advisor detail. One more screen shows the chat under another bank brand.
Writes PNGs under ``docs/build/screenshots/ui-product/``.

Usage, from the repository root::

    python3 scripts/capture_ui_product.py [output-folder]

Chromium is taken from the Playwright cache when present, otherwise
``SENTINEL_CHROME`` or the first ``chromium`` on PATH. The app runs on a
throwaway port with the memory backend and the Gold mock, so no data or
database is touched.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORE = REPO / "sentinel-ai-core"
OUT = REPO / "docs" / "build" / "screenshots" / "ui-product"
PORT = 8123
BRAND_PORT = 8124
BASE = f"http://127.0.0.1:{PORT}"
BRAND_BASE = f"http://127.0.0.1:{BRAND_PORT}"
# A second bank for the "white label" slide. The accent passes the contrast check.
BRAND_ENV = {"SENTINEL_BRAND_NAME": "Banco Aurora", "SENTINEL_BRAND_ACCENT": "#0b6e4f"}

# locale -> demo persona that opens the case in that interface language.
LOCALES = {"es-MX": "normal", "pt-BR": "ambiguous"}
VIEWPORTS = {"desktop": {"width": 1280, "height": 900}, "phone": {"width": 390, "height": 844}}
CUSTOMER_PASSWORD = "Testpass-001"
ADVISOR_PASSWORD = "Advisor-001"


def chrome_path() -> str:
    env = os.environ.get("SENTINEL_CHROME")
    if env:
        return env
    cache = Path.home() / ".cache" / "ms-playwright"
    for candidate in sorted(cache.glob("chromium-*/chrome-linux64/chrome"), reverse=True):
        if candidate.is_file():
            return str(candidate)
    found = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if not found:
        raise SystemExit("No Chromium found; set SENTINEL_CHROME")
    return found


def wait_health(base: str = BASE, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base}/api/v1/health", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:  # noqa: BLE001 - keep polling until the deadline
            time.sleep(0.3)
    raise SystemExit("The app did not become healthy")


def open_case(page) -> None:
    """Wait for the reply to the first chip. A confirm box means the case can open; the
    ambiguous persona gets a question instead, and the screen shows that."""
    # The steps run one second each and the answer follows the last step.
    page.wait_for_selector('[data-testid="steps-panel"] li', state="attached")
    page.wait_for_selector('#steps-side[aria-busy="false"]', state="attached", timeout=20000)
    page.wait_for_timeout(600)
    if page.locator(".chat-confirm button").count():
        page.click(".chat-confirm button")
        page.wait_for_selector('[data-case-state="in_review"]', state="attached", timeout=20000)
        page.wait_for_selector('#steps-side[aria-busy="false"]', state="attached", timeout=20000)
        page.wait_for_timeout(600)


def capture(locale: str, persona: str, size: str) -> None:
    from playwright.sync_api import sync_playwright

    viewport = VIEWPORTS[size]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=chrome_path(), args=["--no-sandbox"]
        )
        context = browser.new_context(viewport=viewport)
        page = context.new_page()

        def shot(name: str) -> None:
            page.screenshot(path=str(OUT / f"{name}-{locale}-{size}.png"), full_page=True, animations="disabled")

        page.goto(f"{BASE}/ui/", wait_until="networkidle")
        page.click(f'[data-locale="{locale}"]')
        page.wait_for_timeout(150)
        shot("entry")

        # Customer: open the persona, open a case, and show the three columns.
        page.click(f'[data-persona="{persona}"]')
        page.wait_for_selector("#demo-prompts:not([hidden])")
        page.click("#demo-prompts .candidate")  # normal case chip
        open_case(page)
        shot("chat")

        # Escalate so the advisor has a ticket and the thread shows the handoff card.
        person = page.locator("#demo-prompts .candidate").last
        person.click()
        page.wait_for_selector('#steps-side[aria-busy="false"]', state="attached", timeout=20000)
        page.wait_for_timeout(1500)
        person.click()
        page.wait_for_selector('[data-testid="handoff-card"]', timeout=20000)
        shot("chat-handoff")
        page.click("#logout")
        page.wait_for_selector("#view-login:not([hidden])")

        # Advisor: list, then the detail with the package and the trace.
        page.click("#password-login > summary")
        page.fill("#login-user", "ADV-0001")
        page.fill("#login-pass", ADVISOR_PASSWORD)
        page.click('#login-form button[type="submit"]')
        page.wait_for_selector('[data-testid="queue-row"]')
        shot("advisor-list")
        page.click('[data-testid="queue-row"]')
        page.wait_for_selector('[data-testid="queue-detail"]:not([hidden])')
        shot("advisor-detail")

        context.close()
        browser.close()


def capture_brand(size: str) -> None:
    """The chat under another bank name and accent, for the white-label slide."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=chrome_path(), args=["--no-sandbox"])
        page = browser.new_context(viewport=VIEWPORTS[size]).new_page()
        page.goto(f"{BRAND_BASE}/ui/", wait_until="networkidle")
        page.click('[data-locale="es-MX"]')
        page.click('[data-persona="normal"]')
        page.wait_for_selector("#demo-prompts:not([hidden])")
        page.click("#demo-prompts .candidate")
        open_case(page)
        page.screenshot(path=str(OUT / f"chat-brand-es-MX-{size}.png"), full_page=True, animations="disabled")
        browser.close()


def start(port: int, extra: dict[str, str]) -> subprocess.Popen:
    env = {
        **os.environ,
        "SENTINEL_DEMO_AUTH": "1",
        "SENTINEL_STATE_BACKEND": "memory",
        "SENTINEL_GOLD_SOURCE": "mock",
        "SENTINEL_SECURE_COOKIES": "false",
        **extra,
    }
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=str(CORE),
        env=env,
    )


def main() -> int:
    global OUT
    if len(sys.argv) > 1:
        OUT = Path(sys.argv[1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    # One fresh app per screen set: the memory state starts empty, so a case opened
    # in one capture never shows in the next.
    runs = [
        (PORT, {}, lambda l=locale, p=persona, z=size: capture(l, p, z))
        for locale, persona in LOCALES.items()
        for size in VIEWPORTS
    ]
    runs += [(BRAND_PORT, BRAND_ENV, lambda z=size: capture_brand(z)) for size in VIEWPORTS]
    for port, extra, run in runs:
        server = start(port, {"SENTINEL_BRAND_NAME": "", "SENTINEL_BRAND_ACCENT": "", **extra})
        try:
            wait_health(f"http://127.0.0.1:{port}")
            run()
        finally:
            server.send_signal(signal.SIGINT)
            server.wait(timeout=10)
    print(f"Wrote screenshots to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
