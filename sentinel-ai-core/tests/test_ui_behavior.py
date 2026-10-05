"""Page behavior in a real browser (change ui-behavior, tasks 2.1 to 2.3).

The tests start the app on a free local port and drive it with headless
Chromium. They skip when Playwright or its browser is not installed, so the
suite stays green on a machine without them.
"""

import json
import os
import socket
import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
uvicorn = pytest.importorskip("uvicorn")
from playwright.sync_api import Error as PlaywrightError  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from app.main import create_app  # noqa: E402

STATIC = Path(__file__).parent.parent / "app" / "static"
PASSWORD = "Testpass-001"
ADVISOR_PASSWORD = "Advisor-001"


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="module")
def base_url():  # type: ignore[no-untyped-def]
    previous = os.environ.get("SENTINEL_DEMO_AUTH")
    os.environ["SENTINEL_DEMO_AUTH"] = "1"
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(create_app(), host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    assert server.started, "the app did not start"
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)
    if previous is None:
        os.environ.pop("SENTINEL_DEMO_AUTH", None)
    else:
        os.environ["SENTINEL_DEMO_AUTH"] = previous


@pytest.fixture(scope="module")
def browser():  # type: ignore[no-untyped-def]
    with sync_playwright() as playwright:
        try:
            chromium = playwright.chromium.launch()
        except PlaywrightError as error:  # browser binary missing
            pytest.skip(f"Chromium is not available: {error}")
        yield chromium
        chromium.close()


@pytest.fixture
def page(browser, base_url):  # type: ignore[no-untyped-def]
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{base_url}/ui/")
    page.wait_for_selector("#login-pass")
    yield page
    assert errors == [], f"the page raised errors: {errors}"
    context.close()


def _customer_login(page, login: str = "CUST-0001") -> None:  # type: ignore[no-untyped-def]
    page.fill("#login-user", login)
    page.fill("#login-pass", PASSWORD)
    page.click("#login-form button[type=submit]")
    page.wait_for_selector("#view-chat:not([hidden]) .tx-card")


def _strings(locale: str) -> dict:
    return json.loads((STATIC / "i18n" / f"{locale}.json").read_text(encoding="utf-8"))


# --- 2.1 One click starts one turn -------------------------------------------


def test_double_click_sends_one_turn_and_a_failed_turn_unlocks(page) -> None:  # type: ignore[no-untyped-def]
    _customer_login(page)
    held: list = []
    # Hold the request: the turn stays in flight while the test clicks again.
    page.route("**/api/v1/chat", lambda route: held.append(route))

    page.dblclick("#agent")
    page.wait_for_timeout(300)
    assert len(held) == 1, "a double click must send one turn"
    assert page.is_disabled("#agent")
    assert page.is_disabled("#chat-input")
    assert page.is_disabled("#chat-form button")

    held[0].fulfill(status=500, content_type="application/json", body="{}")
    page.wait_for_selector("#chat-input:not([disabled])")
    assert not page.is_disabled("#agent")
    assert not page.is_disabled("#chat-form button")


def test_a_closed_connection_unlocks_the_controls(page) -> None:  # type: ignore[no-untyped-def]
    _customer_login(page)
    page.route("**/api/v1/chat", lambda route: route.abort())
    page.click("#agent")
    page.wait_for_selector("#chat-input:not([disabled])")
    assert not page.is_disabled("#agent")
    # The thread says that the turn failed, and the page raises no error.
    page.wait_for_selector("#thread .msg-audit")


# --- 2.2 Language ------------------------------------------------------------


def test_welcome_of_a_persona_shows_in_its_language(page) -> None:  # type: ignore[no-untyped-def]
    page.click('[data-persona="ambiguous"]')  # a pt-BR writer
    page.wait_for_selector("#view-chat:not([hidden]) .tx-card")
    expected = _strings("pt-BR")["welcome"]
    page.wait_for_selector(f'#thread .msg-bot:has-text("{expected[:20]}")')
    assert page.inner_text("#thread .msg-bot").strip() == expected


def test_only_the_last_locale_request_counts(page) -> None:  # type: ignore[no-untyped-def]
    held: list = []
    page.route("**/i18n/pt-BR", lambda route: held.append(route))
    page.click('[data-locale="pt-BR"]')  # slow answer, held
    page.click('[data-locale="es-MX"]')  # fast answer, wins
    page.wait_for_selector('html[lang="es-MX"]', state="attached")
    assert held, "the pt-BR request must have been sent"
    held[0].continue_()  # the old answer arrives late
    page.wait_for_timeout(500)
    assert page.evaluate("document.documentElement.lang") == "es-MX"
    assert page.get_attribute('[data-locale="es-MX"]', "aria-pressed") == "true"
    assert page.get_attribute('[data-locale="pt-BR"]', "aria-pressed") == "false"


def test_raw_keys_stay_hidden_until_the_first_locale_loads(browser, base_url) -> None:  # type: ignore[no-untyped-def]
    context = browser.new_context()
    page = context.new_page()
    held: list = []
    page.route("**/i18n/es-419", lambda route: held.append(route))
    page.goto(f"{base_url}/ui/")
    page.wait_for_timeout(500)
    assert page.evaluate("document.body.hasAttribute('data-loading')")
    assert page.evaluate("getComputedStyle(document.querySelector('main')).visibility") == "hidden"
    assert held, "the first locale request must be pending"
    held[0].continue_()
    page.wait_for_selector("body:not([data-loading])", state="attached")
    assert page.evaluate("getComputedStyle(document.querySelector('main')).visibility") == "visible"
    context.close()


# --- 2.3 Closed turns and advisor names --------------------------------------


def test_chips_of_a_closed_turn_are_disabled(page) -> None:  # type: ignore[no-untyped-def]
    _customer_login(page)
    # Two charges share this merchant, so the system asks which one.
    page.fill("#chat-input", "ACME Store")
    page.press("#chat-input", "Enter")
    page.wait_for_selector("#thread .msg-audit .candidate:not([disabled])", timeout=20000)
    page.wait_for_selector("#chat-input:not([disabled])", timeout=20000)
    # Only the chips of the first question: the later turn may ask a new one.
    first_question = page.locator("#thread .msg-audit").filter(has=page.locator(".candidate")).first
    chips = first_question.locator(".candidate")
    assert chips.count() >= 2

    page.fill("#chat-input", "hola")  # a later turn closes the open question
    page.press("#chat-input", "Enter")
    page.wait_for_selector("#chat-input:not([disabled])", timeout=20000)
    page.wait_for_timeout(300)
    for index in range(chips.count()):
        assert chips.nth(index).is_disabled(), "an old chip must stay disabled"


def test_advisor_view_shows_names_not_codes(browser, base_url) -> None:  # type: ignore[no-untyped-def]
    # A customer asks for a person twice, so a ticket exists.
    customer = browser.new_context()
    api = customer.request
    base = base_url
    assert api.post(f"{base}/api/v1/auth/login", data={"login": "CUST-0001", "password": PASSWORD}).ok
    api.post(f"{base}/api/v1/chat", data={"message": "quiero una persona"})
    assert api.post(f"{base}/api/v1/chat", data={"message": "quiero una persona"}).json()["kind"] == "handoff"
    customer.close()

    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.goto(f"{base}/ui/")
    page.fill("#login-user", "ADV-0001")
    page.fill("#login-pass", ADVISOR_PASSWORD)
    page.click("#login-form button[type=submit]")
    page.wait_for_selector(".queue-row")
    row = page.locator(".queue-row").first.inner_text()
    es = _strings("es-419")
    assert es["country.MX"] in row, row
    assert es["lang.es-419"] in row, row
    assert "es-419" not in row and "MX" not in row.replace("México", ""), "codes must not show"
    page.locator(".queue-row").first.click()
    page.wait_for_selector("#tab-json")
    page.click("#tab-json")
    shown = page.inner_text("[data-testid=json-view]")
    assert "customer_id" not in shown, "the advisor JSON must not carry the customer id"
    context.close()
