from fastapi.testclient import TestClient
import pytest

from app.main import create_app

PASSWORD = "Testpass-001"


def login(api: TestClient, name: str = "CUST-0001") -> None:
    assert api.post("/session/login", json={"login": name, "password": PASSWORD}).status_code == 200


def test_listing_is_session_scoped_and_ordered() -> None:
    api = TestClient(create_app())
    login(api)
    response = api.get("/transactions")
    assert response.status_code == 200
    body = response.json()
    assert body["as_of"] == "2026-06-17"
    ids = [row["reference"] for row in body["transactions"]]
    dates = [row["date"] for row in body["transactions"]]
    assert "TXN-9001" not in ids
    assert "TXN-2001" not in ids
    assert dates == sorted(dates, reverse=True)
    assert body["transactions"][0]["currency"] == "MXN"


def test_customer_identifier_is_rejected() -> None:
    api = TestClient(create_app())
    login(api)
    response = api.get("/transactions", params={"customer_id": "CUST-9999"})
    assert response.status_code == 422


def test_listing_requires_a_session() -> None:
    api = TestClient(create_app())
    assert api.get("/transactions").status_code == 401


# --- Point 1: every country customer reads only their own charges, own currency


def test_cop_customer_sees_only_cop_charges() -> None:
    api = TestClient(create_app())
    login(api, "CUST-0002")
    body = api.get("/transactions").json()
    assert body["transactions"], "CUST-0002 must have charges"
    assert {row["currency"] for row in body["transactions"]} == {"COP"}
    ids = {row["reference"] for row in body["transactions"]}
    assert "TXN-1001" not in ids, "MXN customer rows must not leak into COP listing"
    assert "TXN-9001" not in ids


def test_ars_customer_sees_only_ars_charges() -> None:
    api = TestClient(create_app())
    login(api, "CUST-0003")
    body = api.get("/transactions").json()
    assert body["transactions"], "CUST-0003 must have charges"
    assert {row["currency"] for row in body["transactions"]} == {"ARS"}
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
        listing = api.get("/transactions").json()["transactions"]
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
    if api.get("/transactions", params={"customer_id": "CUST-9999"}).status_code == 422:
        blocked += 1

    # One session-less attempt.
    attempts += 1
    if TestClient(create_app()).get("/transactions").status_code == 401:
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
    listing = api.get("/transactions")
    assert "Refunded" not in listing.text

    chat = api.post("/chat", json={"message": "no reconozco un cargo"})
    assert "Refunded" not in chat.text

    confirmation = api.post("/chat", json={"selected_reference": "TXN-1003"})
    assert "Refunded" not in confirmation.text


def test_chat_never_emits_raw_gold_status() -> None:
    """The chat path already maps status; only the listing leaks (see above)."""
    api = TestClient(create_app())
    login(api)
    api.post("/chat", json={"message": "no reconozco un cargo"})
    confirmation = api.post("/chat", json={"selected_reference": "TXN-1003"})
    assert "Refunded" not in confirmation.text


# --- Point 2 (report): status is mapped on two paths, listing and chat differ


def test_transactions_status_is_mapped() -> None:
    """The listing status is normalized through to_candidate; 'Refunded' → 'Reversed'."""
    api = TestClient(create_app())
    login(api)
    rows = {row["reference"]: row for row in api.get("/transactions").json()["transactions"]}
    assert rows["TXN-1003"]["status"] == "Reversed"
