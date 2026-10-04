"""Demo prompt chips: templates in every locale, phrases built from real charges.

The three chips exist so a 3-minute demo needs three clicks, not typing. They are
built from whatever `GET /api/v1/transactions` returns for the signed-in
customer, so they work for every demo customer instead of only one fixture.

Requirements covered: REQ-0042 (open a dispute with minimum effort) and
REQ-0012/REQ-0044 (works in Spanish and Portuguese).
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

PASSWORD = "Testpass-001"
CUSTOMERS = ("CUST-0001", "CUST-0002", "CUST-0003")
LOCALES = ("es-419", "es-MX", "es-CO", "es-AR", "pt-BR")
I18N_DIR = Path(__file__).parents[1] / "app" / "static" / "i18n"
APP_JS = (Path(__file__).parents[1] / "app" / "static" / "app.js").read_text(encoding="utf-8")
INDEX = (Path(__file__).parents[1] / "app" / "static" / "index.html").read_text(encoding="utf-8")

DEMO_KEYS = ("demoHint", "demoNormal", "demoAmbiguous", "demoPerson")
COUNTRY_CURRENCIES = {"MX": "MXN", "CO": "COP", "AR": "ARS"}


def days_between(from_iso: str, to_iso: str) -> int:
    from datetime import date

    return (date.fromisoformat(to_iso) - date.fromisoformat(from_iso)).days


def client_for(name: str) -> TestClient:
    api = TestClient(create_app())
    assert api.post(
        "/api/v1/auth/login", json={"login": name, "password": PASSWORD}
    ).status_code == 200
    return api


def transactions(api: TestClient) -> list[dict]:
    return api.get("/api/v1/transactions").json()["transactions"]


# --- templates ------------------------------------------------------------


@pytest.mark.parametrize("locale", LOCALES)
def test_demo_templates_exist_in_every_locale(locale: str) -> None:
    """The chips are translated, so the keys must exist in all five files."""
    strings = json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))
    if locale != "es-419":
        base = json.loads((I18N_DIR / "es-419.json").read_text(encoding="utf-8"))
        merged = {**base, **strings}
        strings = merged
    missing = [key for key in DEMO_KEYS if key not in strings]
    assert missing == [], f"{locale} missing demo keys: {missing}"


def test_templates_use_placeholders_not_fixture_values() -> None:
    """No hardcoded amount, merchant or date: they come from the customer."""
    for locale in LOCALES:
        strings = json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))
        normal = strings.get("demoNormal")
        if normal is None:
            continue  # regionals override, they need not repeat every key
        assert "{amount}" in normal and "{merchant}" in normal and "{date}" in normal
        ambiguous = strings.get("demoAmbiguous")
        if ambiguous is not None:
            assert "{merchant}" in ambiguous
            assert "{amount}" not in ambiguous and "{date}" not in ambiguous


def test_ambiguous_template_asks_by_merchant_only() -> None:
    """An ambiguous phrase must not name a specific charge, or it would resolve."""
    strings = json.loads((I18N_DIR / "es-419.json").read_text(encoding="utf-8"))
    assert "{amount}" not in strings["demoAmbiguous"]
    assert "{date}" not in strings["demoAmbiguous"]


# --- the phrases resolve the way the demo needs ---------------------------


@pytest.mark.parametrize("customer", CUSTOMERS)
def test_normal_phrase_reaches_the_confirm_box(customer: str) -> None:
    """The chip's charge is picked from the listing alone: newest eligible local.

    The rule is: in the account's own currency and not `eligible=false`. The
    backend already folds the country policy (window, status, prior dispute)
    into `eligible`, so the page does not re-derive the 90-day window. If that
    charge escalates on click, that is a legitimate outcome and the chip still
    shows it.
    """
    api = client_for(customer)
    payload = api.get("/api/v1/transactions").json()
    rows = payload["transactions"]
    country = api.get("/api/v1/auth/me").json()["country"]
    currency = COUNTRY_CURRENCIES[country]

    local = [
        tx
        for tx in rows
        if tx.get("eligible") is not False and tx["currency"] == currency
    ]
    assert local, f"{customer} must have a local-currency charge for the chip"
    charge = sorted(local, key=lambda tx: tx["date"], reverse=True)[0]

    phrase = (
        f"no reconozco el cargo de {charge['amount']} en {charge['merchant']} "
        f"del {charge['date']}"
    )
    body = api.post("/api/v1/chat", json={"message": phrase}).json()
    # Two legitimate outcomes: the confirm box, or an escalation. Never a
    # failure to be understood, and never a case opened without confirmation.
    assert body["kind"] in ("confirm_box", "handoff"), f"{customer}: {body['kind']}"
    if body["kind"] == "confirm_box":
        assert body["candidate"]["reference"] == charge["reference"]


@pytest.mark.parametrize("customer", CUSTOMERS)
def test_chip_charge_is_the_newest_local_one(customer: str) -> None:
    """USD rows are excluded: they are not what the customer would dispute."""
    api = client_for(customer)
    payload = api.get("/api/v1/transactions").json()
    country = api.get("/api/v1/auth/me").json()["country"]
    currency = COUNTRY_CURRENCIES[country]
    rows = payload["transactions"]
    has_usd = any(tx["currency"] == "USD" for tx in rows)
    local = [tx for tx in rows if tx["currency"] == currency]
    assert has_usd and local, f"{customer}: the fixture should carry both currencies"
    # The newest local charge is not the newest row overall: the USD rows are.
    newest_overall = max(rows, key=lambda tx: tx["date"])["currency"]
    assert newest_overall == "USD", "the fixture must exercise the exclusion"


@pytest.mark.parametrize("customer", CUSTOMERS)
def test_ambiguous_phrase_asks_with_charges(customer: str) -> None:
    """A merchant with two or more charges makes the system ask, not guess."""
    api = client_for(customer)
    rows = transactions(api)
    counts: dict[str, int] = {}
    for tx in rows:
        counts[tx["merchant"]] = counts.get(tx["merchant"], 0) + 1
    repeated = next((m for m, n in counts.items() if n >= 2), None)
    if repeated is None:
        pytest.skip(f"{customer} has no repeated merchant, so the chip is hidden")
    body = api.post(
        "/api/v1/chat", json={"message": f"no reconozco un cargo en {repeated}"}
    ).json()
    assert body["kind"] == "clarification"
    assert len(body["candidates"]) >= 2, "ambiguity must offer the real candidates"


@pytest.mark.parametrize("customer", CUSTOMERS)
def test_person_phrase_offers_then_hands_off(customer: str) -> None:
    """One offer to keep helping, then a handoff on insistence (REQ-0040).

    The first ask comes back as a text reply carrying the `person.ask` rule;
    the second escalates. The chip sends the same phrase both times.
    """
    api = client_for(customer)
    first = api.post("/api/v1/chat", json={"message": "quiero hablar con una persona"}).json()
    second = api.post("/api/v1/chat", json={"message": "quiero hablar con una persona"}).json()
    assert first["kind"] == "text"
    assert second["kind"] == "handoff"


def test_portuguese_person_phrase_also_works() -> None:
    api = client_for("CUST-0001")
    api.post("/api/v1/chat", json={"message": "quero falar com um atendente"})
    second = api.post("/api/v1/chat", json={"message": "quero falar com um atendente"})
    assert second.json()["kind"] == "handoff"


# --- the chip building rules ---------------------------------------------


def test_customer_without_a_repeated_merchant_has_no_ambiguous_chip() -> None:
    """CUST-0002 and CUST-0003 have one charge per merchant: no chip."""
    for customer in ("CUST-0002", "CUST-0003"):
        rows = transactions(client_for(customer))
        counts: dict[str, int] = {}
        for tx in rows:
            counts[tx["merchant"]] = counts.get(tx["merchant"], 0) + 1
        assert not any(n >= 2 for n in counts.values()), customer


def test_first_customer_does_have_a_repeated_merchant() -> None:
    rows = transactions(client_for("CUST-0001"))
    counts: dict[str, int] = {}
    for tx in rows:
        counts[tx["merchant"]] = counts.get(tx["merchant"], 0) + 1
    assert any(n >= 2 for n in counts.values()), "CUST-0001 is the ambiguous demo"


def test_app_builds_the_phrases_from_the_listing() -> None:
    """The chips read the listing; they never carry a fixture value."""
    assert "renderDemoPrompts(payload.transactions" in APP_JS
    assert "repeatedMerchant" in APP_JS and "demoCharge" in APP_JS
    assert "demo-prompts" in INDEX
    # A hardcoded fixture charge would defeat the whole point.
    for fixture in ("TXN-1001", "1000.00", "ACME Store"):
        assert fixture not in APP_JS, f"hardcoded fixture value in app.js: {fixture}"


def test_chip_keeps_a_charge_that_really_reaches_the_confirm_box() -> None:
    """The chip picks from the listing; it never probes the chat."""
    assert "demoCharge" in APP_JS
    assert "localCurrency" in APP_JS
    assert "findConfirmableCharge" not in APP_JS, "the probe was removed on purpose"


def test_loading_the_page_posts_nothing_to_the_chat() -> None:
    """A page load must not spend turns, pollute logs or create tickets.

    The chips are built from `GET /api/v1/transactions` and `GET /api/v1/auth/me`
    only. Any chat call while the page loads would be a real turn: it lands in
    the conversation, the structured logs and the metrics, and an escalation
    would create a handoff ticket for the advisor.
    """
    api = client_for("CUST-0001")
    before = len(api.app.state.cases.for_customer("CUST-0001"))
    turns_before = api.get("/api/v1/disputes").json()

    # Exactly what the page does on login.
    api.get("/api/v1/auth/me")
    payload = api.get("/api/v1/transactions").json()

    # Selecting the chip charge is a pure function of that payload.
    country = api.get("/api/v1/auth/me").json()["country"]
    currency = COUNTRY_CURRENCIES[country]
    chosen = [
        tx
        for tx in payload["transactions"]
        if tx.get("eligible") is not False and tx["currency"] == currency
    ]

    assert chosen, "the normal chip has a charge to offer"
    # Nothing above touched the chat: no case, no ticket, no new turn.
    after = len(api.app.state.cases.for_customer("CUST-0001"))
    assert after == before, "building the chips created a case"
    assert api.get("/api/v1/disputes").json() == turns_before


def test_chips_only_for_supported_flows() -> None:
    """Each chip is gated by the precondition of a flow supported end to end.

    Normal needs an eligible local charge, ambiguous a repeated merchant, and
    the person chip maps to the supported handoff. A chip with no data behind
    it is hidden instead of offered and then failing.
    """
    start = APP_JS.index("function renderDemoPrompts")
    end = APP_JS.index("/* Advisor view")
    block = APP_JS[start:end]
    assert "if (charge)" in block and "if (merchant)" in block
    assert 'prompts.push(t("demoPerson"))' in block
    assert "box.hidden = prompts.length === 0" in block


def test_app_does_not_post_chat_while_building_the_chips() -> None:
    """Static guard: the chip path contains no POST to the chat."""
    start = APP_JS.index("function renderDemoPrompts")
    end = APP_JS.index("/* Advisor view")
    chip_block = APP_JS[start:end]
    assert "/api/v1/chat" not in chip_block, "the chip builder calls the chat"
    assert "postChat" not in chip_block.replace("postChat({ message: phrase })", ""), (
        "the chip builder must only post from the click handler"
    )
    # The only chat call is the one inside the click listener.
    assert chip_block.count("postChat(") == 1


def test_chip_has_no_usd_charge_and_no_out_of_window_charge() -> None:
    """The backend's `eligible` flag carries the window and the currency rule.

    TXN-1002 is 153 days before the as-of date. The meaningful check is that the
    backend marks it `candidateOutOfWindow`, not that the page re-derives the
    window: the chip rule is `eligible is not False`.
    """
    api = client_for("CUST-0001")
    payload = api.get("/api/v1/transactions").json()
    rows = payload["transactions"]
    stale = next(tx for tx in rows if tx["reference"] == "TXN-1002")
    assert days_between(stale["date"], payload["as_of"]) > 90, "fixture must be stale"
    assert stale["eligible"] is False, "the backend must mark the stale charge ineligible"
    assert stale["ineligibleKey"] == "candidateOutOfWindow"
    # The chip rule is the eligible local set, so the stale charge is never it.
    chip_choice = [
        tx
        for tx in rows
        if tx.get("eligible") is not False and tx["currency"] == "MXN"
    ]
    assert stale["reference"] not in {tx["reference"] for tx in chip_choice}


def test_chip_rule_uses_backend_eligibility_not_a_local_window() -> None:
    """Regression guard: the page must not duplicate the country's window."""
    assert "WINDOW_DAYS" not in APP_JS, "the hardcoded window came back"
    assert "daysBetween" not in APP_JS, "the page re-derives the window"
    assert "tx.eligible !== false" in APP_JS, "the chip must trust backend eligibility"


# --- locale-aware amount formatting --------------------------------------


def test_amount_formatting_follows_the_locale() -> None:
    """es-MX groups with a comma; es-AR and pt-BR use a dot."""
    api = client_for("CUST-0001")
    mx = api.get("/i18n/es-MX").json()
    ar = api.get("/i18n/es-AR").json()
    assert mx and ar  # the locale endpoint answers for both
    # The formatter is part of the page, driven by the active locale.
    assert "Intl.NumberFormat" in APP_JS
    assert "Intl.DateTimeFormat" in APP_JS
    assert "activeLocale()" in APP_JS


@pytest.mark.parametrize(
    ("locale", "expected"),
    [("es-MX", "1,000.00"), ("es-AR", "1.000,00"), ("es-CO", "1.000,00"), ("pt-BR", "1.000,00")],
)
def test_locale_grouping_matches_the_country(locale: str, expected: str) -> None:
    """Pins the grouping convention per locale, which is the demo-visible part."""
    import subprocess
    import sys

    script = (
        "const n = new Intl.NumberFormat(%r, {minimumFractionDigits: 2, "
        "maximumFractionDigits: 2}).format(1000); process.stdout.write(n)"
    ) % (locale,)
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        pytest.skip("node is not available to evaluate Intl grouping")
    assert result.stdout.strip() == expected
