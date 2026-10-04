#!/usr/bin/env python3
"""Capture the ui-product screens for the deliverable.

Four screens (entry, chat with the resolution panel, advisor list, advisor
detail) in es-MX and pt-BR, at desktop and phone width, against a running app
in demo mode. Writes PNGs under ``docs/build/screenshots/ui-product/``.

Usage, from the repository root::

    python3 scripts/capture_ui_product.py

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
BASE = f"http://127.0.0.1:{PORT}"

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


def wait_health(timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/api/v1/health", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:  # noqa: BLE001 - keep polling until the deadline
            time.sleep(0.3)
    raise SystemExit("The app did not become healthy")


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
            page.screenshot(path=str(OUT / f"{name}-{locale}-{size}.png"), full_page=True)

        page.goto(f"{BASE}/ui/", wait_until="networkidle")
        page.click(f'[data-locale="{locale}"]')
        page.wait_for_timeout(150)
        shot("entry")

        # Customer: open the persona and take a turn that shows the panel.
        page.click(f'[data-persona="{persona}"]')
        page.wait_for_selector("#demo-prompts:not([hidden])")
        page.click("#demo-prompts .candidate")  # normal case chip
        page.wait_for_selector('[data-testid="steps-panel"]')
        shot("chat")

        # Escalate so the advisor has a ticket to open.
        person = page.locator("#demo-prompts .candidate").last
        person.click()
        page.wait_for_timeout(200)
        person.click()
        page.wait_for_selector('text=HO-', timeout=5000)
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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "SENTINEL_DEMO_AUTH": "1",
        "SENTINEL_STATE_BACKEND": "memory",
        "SENTINEL_GOLD_SOURCE": "mock",
        "SENTINEL_SECURE_COOKIES": "false",
    }
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORT), "--log-level", "warning"],
        cwd=str(CORE),
        env=env,
    )
    try:
        wait_health()
        for locale, persona in LOCALES.items():
            for size in VIEWPORTS:
                capture(locale, persona, size)
    finally:
        server.send_signal(signal.SIGINT)
        server.wait(timeout=10)
    print(f"Wrote screenshots to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
