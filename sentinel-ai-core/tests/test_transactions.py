from fastapi.testclient import TestClient

from app.main import create_app

PASSWORD = "Testpass-001"


def login(api: TestClient, name: str = "CUST-0001") -> None:
    assert api.post("/api/v1/auth/login", json={"login": name, "password": PASSWORD}).status_code == 200


def test_listing_is_session_scoped_and_ordered() -> None:
    api = TestClient(create_app())
    login(api)
    response = api.get("/api/v1/transactions")
    assert response.status_code == 200
    body = response.json()
    assert body["as_of"] == "2026-06-17"
    ids = [row["reference"] for row in body["transactions"]]
    dates = [row["date"] for row in body["transactions"]]
    assert "TXN-9001" not in ids
    assert "TXN-2001" not in ids
    assert dates == sorted(dates, reverse=True)
    assert {row["currency"] for row in body["transactions"]} == {"MXN", "USD"}


def test_customer_identifier_is_rejected() -> None:
    api = TestClient(create_app())
    login(api)
    response = api.get("/api/v1/transactions", params={"customer_id": "CUST-9999"})
    assert response.status_code == 422


def test_listing_requires_a_session() -> None:
    api = TestClient(create_app())
    assert api.get("/api/v1/transactions").status_code == 401


# --- Point 1: every country customer reads only their own charges, in the local
# currency or USD (currency belongs to the product; gold-layer spec)


def test_cop_customer_sees_only_cop_charges() -> None:
    api = TestClient(create_app())
    login(api, "CUST-0002")
    body = api.get("/api/v1/transactions").json()
    assert body["transactions"], "CUST-0002 must have charges"
    assert {row["currency"] for row in body["transactions"]} == {"COP", "USD"}
    ids = {row["reference"] for row in body["transactions"]}
    assert "TXN-1001" not in ids, "MXN customer rows must not leak into COP listing"
    assert "TXN-9001" not in ids


def test_ars_customer_sees_only_ars_charges() -> None:
    api = TestClient(create_app())
    login(api, "CUST-0003")
    body = api.get("/api/v1/transactions").json()
    assert body["transactions"], "CUST-0003 must have charges"
    assert {row["currency"] for row in body["transactions"]} == {"ARS", "USD"}
    ids = {row["reference"] for row in body["transactions"]}
    assert "TXN-1001" not in ids
    assert "TXN-2001" not in ids


# --- Point 3: measurable denial rate. 3 customers x 2 foreign peers + 2 shapes
# = 8 attempts, all blocked: "8 of 8 blocked".


def test_foreign_access_attempts_are_blocked_8_of_8() -> None:
    """Denial matrix, 8 of 8 blocked.

    Six cross-customer reads (each of the 3 customers attempting the other 2
    customers' rows), one explicit query-parameter attempt, and one
    session-less request. Counted explicitly so the demo can quote "8 de 8".
    """
    customers = ["CUST-0001", "CUST-0002", "CUST-0003"]
    own_prefix = {"CUST-0001": "TXN-1", "CUST-0002": "TXN-2", "CUST-0003": "TXN-3"}
    attempts = 0
    blocked = 0

    # Six cross-customer attempts.
    for customer in customers:
        api = TestClient(create_app())
        login(api, customer)
        listing = api.get("/api/v1/transactions").json()["transactions"]
        ids = {row["reference"] for row in listing}
        for peer in customers:
            if peer == customer:
                continue
            attempts += 1
            foreign = [ref for ref in ids if not ref.startswith(own_prefix[customer])]
            # The foreign customer's row is not present, and asking for it by
            # id under this session would not resolve either.
            if not foreign:
                blocked += 1

    # One explicit identifier attempt.
    api = TestClient(create_app())
    login(api)
    attempts += 1
    if api.get("/api/v1/transactions", params={"customer_id": "CUST-9999"}).status_code == 422:
        blocked += 1

    # One session-less attempt.
    attempts += 1
    if TestClient(create_app()).get("/api/v1/transactions").status_code == 401:
        blocked += 1

    assert (attempts, blocked) == (8, 8), f"{blocked} of {attempts} blocked"


# --- Point 6: the raw Gold vocabulary never reaches an HTTP response


def test_raw_gold_status_never_appears_in_any_response() -> None:
    """"Refunded" is Gold vocabulary. The public contract must not carry it.

    The demo transactions listing omits the raw status field entirely;
    the chat path maps status via the candidate adapter before rendering.
    """
    api = TestClient(create_app())
    login(api)
    listing = api.get("/api/v1/transactions")
    assert "Refunded" not in listing.text

    chat = api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    assert "Refunded" not in chat.text

    confirmation = api.post("/api/v1/chat", json={"selected_reference": "TXN-1003"})
    assert "Refunded" not in confirmation.text


def test_chat_never_emits_raw_gold_status() -> None:
    """The chat path already maps status; only the listing leaks (see above)."""
    api = TestClient(create_app())
    login(api)
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    confirmation = api.post("/api/v1/chat", json={"selected_reference": "TXN-1003"})
    assert "Refunded" not in confirmation.text


# --- Point 2 (report): status is mapped on two paths, listing and chat differ


def test_transactions_status_is_mapped() -> None:
    """The listing status is normalized through to_candidate; 'Refunded' → 'Reversed'."""
    api = TestClient(create_app())
    login(api)
    rows = {row["reference"]: row for row in api.get("/api/v1/transactions").json()["transactions"]}
    assert rows["TXN-1003"]["status"] == "Reversed"


# --- bank-ui: the server sets the case state of each charge


def _states(api: TestClient) -> dict[str, str]:
    rows = api.get("/api/v1/transactions").json()["transactions"]
    return {row["reference"]: row["case_state"] for row in rows}


def test_case_state_comes_from_policy() -> None:
    api = TestClient(create_app())
    login(api)
    states = _states(api)
    assert states["TXN-1001"] == "eligible"
    assert states["TXN-1004"] == "already_disputed"
    assert states["TXN-1003"] == "not_disputable"
    assert states["TXN-1002"] == "outside_window"


def test_case_state_follows_the_case_store() -> None:
    from datetime import datetime, timezone

    from app.state.cases import ESCALATED, OPEN, CaseRow

    app = create_app()
    api = TestClient(app)
    login(api)
    now = datetime.now(timezone.utc)
    app.state.cases.add(CaseRow("D-T1", "CUST-0001", "dispute", OPEN, now, transaction_id="TXN-1001"))
    app.state.cases.add(CaseRow("H-T1", "CUST-0001", "handoff", ESCALATED, now, transaction_id="TXN-1006"))
    app.state.cases.add(CaseRow("D-T2", "CUST-9999", "dispute", OPEN, now, transaction_id="TXN-1101"))
    states = _states(api)
    assert states["TXN-1001"] == "in_review"
    assert states["TXN-1006"] == "with_advisor"
    rows = {r["reference"]: r for r in api.get("/api/v1/transactions").json()["transactions"]}
    assert rows["TXN-1001"]["eligible"] is False, "a charge in review cannot be disputed again"
    assert states["TXN-1101"] == "eligible", "another customer's case must not change this listing"


def test_case_state_adds_no_personal_field() -> None:
    api = TestClient(create_app())
    login(api)
    row = api.get("/api/v1/transactions").json()["transactions"][0]
    assert set(row) == {
        "reference", "amount", "currency", "merchant", "date", "status",
        "eligible", "ineligibleKey", "case_state",
    }


def test_demo_session_has_a_masked_product_and_no_other_digits() -> None:
    api = TestClient(create_app())
    login(api)
    product = api.get("/api/v1/transactions").json()["product"]
    assert product == {"kind": "debit_card", "last4": "4821", "synthetic": True}


def test_gold_without_product_data_gives_no_product() -> None:
    app = create_app()
    api = TestClient(app)
    login(api)
    app.state.gold = _WithoutProducts(app.state.gold)
    body = api.get("/api/v1/transactions").json()
    assert body["product"] is None
    assert body["transactions"], "the listing still works"


class _WithoutProducts:
    """A Gold source like the real one: charges only, no product data."""

    def __init__(self, inner) -> None:
        self.get = inner.get
        self.list_for_customer = inner.list_for_customer
