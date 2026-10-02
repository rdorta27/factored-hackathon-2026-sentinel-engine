from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.orchestrator.types import TransactionStatus
from app.tools.bound import SessionBoundLookup
from app.tools.fake import InMemoryTools
from app.tools.gold import GoldRow, MockGoldStore

AS_OF = "2026-06-17"
PASSWORD = "Testpass-001"
STATIC = Path(__file__).parent.parent / "app" / "static"


def login(api: TestClient, name: str = "CUST-0001") -> None:
    assert api.post("/api/v1/auth/login", json={"login": name, "password": PASSWORD}).status_code == 200


def test_lookup_is_bound_and_hides_foreign_rows() -> None:
    gold = MockGoldStore(as_of=AS_OF)
    bound = SessionBoundLookup(gold, "CUST-0001", InMemoryTools())
    rows = bound.lookup_transactions()
    ids = {row.candidate_id for row in rows}
    assert "TXN-9001" not in ids
    assert "TXN-2001" not in ids
    assert all(row.as_of == AS_OF for row in rows)


def test_refunded_maps_to_reversed() -> None:
    gold = MockGoldStore(as_of=AS_OF)
    bound = SessionBoundLookup(gold, "CUST-0001", InMemoryTools())
    refunded = next(row for row in bound.lookup_transactions() if row.candidate_id == "TXN-1003")
    assert refunded.status is TransactionStatus.REVERSED


def test_lookup_transactions_takes_no_customer_argument() -> None:
    bound = SessionBoundLookup(MockGoldStore(as_of=AS_OF), "CUST-0001", InMemoryTools())
    assert bound.lookup_transactions.__code__.co_argcount == 1


def confirm(api: TestClient, reference: str = "TXN-1001") -> dict:
    """Drive the real two-step confirmation: select, then confirm the box."""
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    api.post("/api/v1/chat", json={"selected_reference": reference})
    return api.post("/api/v1/chat", json={"selected_reference": reference}).json()


# --- Point 5: canary. Displayed facts follow the Gold, not generated text.


class CanaryGold:
    """Gold whose rows carry impossible values, to prove the source of truth."""

    def __init__(self, amount: str, merchant: str) -> None:
        self._rows = {
            ("TXN-1001", "CUST-0001"): GoldRow(
                reference="TXN-1001",
                customer_id="CUST-0001",
                amount=amount,
                currency="MXN",
                merchant=merchant,
                date="2026-06-10",
                status="Approved",
                as_of=AS_OF,
            )
        }

    def get(self, reference: str, customer_id: str) -> GoldRow | None:
        return self._rows.get((reference, customer_id))

    def list_for_customer(self, customer_id: str) -> list[GoldRow]:
        return [row for row in self._rows.values() if row.customer_id == customer_id]


def app_with_canary(amount: str, merchant: str):  # type: ignore[no-untyped-def]
    app = create_app()
    app.state.gold = CanaryGold(amount, merchant)
    return app


def test_rendered_facts_follow_gold_not_generated_text() -> None:
    """Canary: impossible facts from Gold must appear, and nothing else may.

    If any displayed amount or merchant could originate in generated text, the
    canary would be absent and this test would fail.
    """
    api = TestClient(app_with_canary("9876.54", "Centinela XYZ"))
    login(api)
    listing = api.get("/api/v1/transactions").json()["transactions"]
    assert len(listing) == 1
    assert listing[0]["amount"] == "9876.54"
    assert listing[0]["merchant"] == "Centinela XYZ"

    confirmation = confirm(api)
    facts = confirmation.get("transaction") or confirmation.get("candidate") or {}
    assert facts.get("amount") == "9876.54", "amount must come from Gold"
    assert facts.get("merchant") == "Centinela XYZ", "merchant must come from Gold"
    rendered = str(confirmation)
    assert "1000.00" not in rendered, "a hardcoded or invented amount leaked"


def test_rendered_facts_change_when_gold_changes() -> None:
    """Reinforcement: a second Gold with different facts must change the reply.

    An assumed (hardcoded) value would be stable across both calls.
    """
    first = TestClient(app_with_canary("1111.11", "Centinela Uno"))
    login(first)
    first_reply = confirm(first)

    second = TestClient(app_with_canary("2222.22", "Centinela Dos"))
    login(second)
    second_reply = confirm(second)

    first_facts = first_reply.get("transaction") or first_reply.get("candidate") or {}
    second_facts = second_reply.get("transaction") or second_reply.get("candidate") or {}
    assert first_facts["amount"] == "1111.11"
    assert second_facts["amount"] == "2222.22"
    assert first_facts["merchant"] != second_facts["merchant"]


# --- Point 2: one reference date for the screen and the engine


def _share_one_reference_date(api: TestClient) -> None:
    login(api)
    listing = api.get("/api/v1/transactions").json()
    confirmation = confirm(api)
    display = confirmation.get("display") or {}
    engine_dates = {listing["as_of"], display.get("referenceDate"), confirmation.get("as_of")}
    engine_dates.discard(None)
    assert len(engine_dates) == 1, f"screen and engine disagree: {engine_dates}"
    return listing["as_of"]


def test_screen_and_engine_share_the_default_reference_date() -> None:
    assert _share_one_reference_date(TestClient(create_app())) == AS_OF


def test_screen_and_engine_share_an_environment_reference_date(
    monkeypatch,  # type: ignore[no-untyped-def]
) -> None:
    monkeypatch.setenv("SENTINEL_REFERENCE_DATE", "2026-03-01")
    api = TestClient(create_app())
    assert api.app.state.reference_date.isoformat() == "2026-03-01"
    assert _share_one_reference_date(api) == "2026-03-01"


# --- Point 4: the internal transaction id is data, never a label


def test_reference_is_never_rendered_by_the_frontend() -> None:
    """`reference` may travel in the JSON, but app.js must not paint the
    internal transaction id. The handoff ticket reference (`HO-…`) is
    customer-facing and does get painted, under `field_reference`."""
    source = (STATIC / "app.js").read_text(encoding="utf-8")
    assert "selected_reference: candidate.reference" in source
    offenders = []
    for line in source.splitlines():
        stripped = line.strip()
        if "reference" not in stripped:
            continue
        if "selected_reference" in stripped:
            continue
        if "field_reference" in stripped:
            continue  # the reference DATE and the handoff ticket reference are translated
        if "el(" in stripped or "textContent" in stripped:
            offenders.append(stripped)
    assert offenders == [], f"reference rendered into text: {offenders}"


def test_listing_exposes_reference_for_the_structured_selection() -> None:
    """The id must travel, because picking a charge sends it back."""
    api = TestClient(create_app())
    login(api)
    rows = api.get("/api/v1/transactions").json()["transactions"]
    assert all(row["reference"].startswith("TXN-") for row in rows)
    assert all("merchant" in row and "amount" in row and "date" in row for row in rows)
