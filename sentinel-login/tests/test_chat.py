"""Chat tests: grounding, candidates, selection, and locale-neutral replies."""

from fastapi.testclient import TestClient

from app.main import create_app

CUSTOMER = ("CUST-0001", "Testpass-001")
EXACT = "I dispute the charge of 1000.00 at ACME Store on 2026-06-10"


def make_customer_client() -> TestClient:
    client = TestClient(create_app())
    assert (
        client.post(
            "/auth/login",
            json={"customer_id": CUSTOMER[0], "password": CUSTOMER[1]},
        ).status_code
        == 200
    )
    return client


def test_normal_case_returns_verified_confirmation() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"message": EXACT})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "case_confirmation"
    assert body["verified"] is True
    assert body["case_id"].startswith("CASE-")
    assert body["transaction"]["amount"] == "1000.00"
    assert body["transaction"]["currency"] == "MXN"
    assert body["transaction"]["merchant"] == "ACME Store"
    assert body["display"]["slaDate"] == "2026-06-19"
    assert body["messages"]["nextStep"] == "nextStepAdvisorReview"
    assert body["source"] == "mock"


def test_wrong_date_never_opens_a_case() -> None:
    """The reported bug: stated date must match the transaction exactly."""
    client = make_customer_client()
    response = client.post(
        "/chat",
        json={"message": "I dispute the charge of 1000.00 at ACME Store on 2026-09-20"},
    )
    body = response.json()
    assert body["kind"] == "clarification"
    assert body["candidates"], "candidates must be offered"
    assert "case_id" not in body
    assert client.app.state.cases._cases == {}


def test_candidates_are_ranked_and_capped() -> None:
    client = make_customer_client()
    body = client.post(
        "/chat",
        json={"message": "I dispute the charge of 1000.00 at ACME Store on 2026-09-20"},
    ).json()
    candidates = body["candidates"]
    assert 1 <= len(candidates) <= 4
    # The two 1000.00 ACME charges come first, before unrelated merchants.
    assert candidates[0]["amount"] == "1000.00"
    assert candidates[0]["merchant"] == "ACME Store"


def test_out_of_window_candidate_is_marked_not_selectable() -> None:
    client = make_customer_client()
    body = client.post(
        "/chat",
        json={"message": "I dispute the charge of 2500.00 at ACME Store on 2026-09-20"},
    ).json()
    stale = [c for c in body["candidates"] if c["date"] == "2026-01-15"]
    if stale:
        assert stale[0]["eligible"] is False
        assert stale[0]["ineligibleKey"] == "candidateOutOfWindow"


def test_selected_reference_opens_that_transaction() -> None:
    """Explicit choice travels as a structured field, not as prose."""
    client = make_customer_client()
    response = client.post("/chat", json={"selected_reference": "TXN-1005"})
    body = response.json()
    assert body["kind"] == "case_confirmation"
    assert body["transaction"]["date"] == "2026-05-20"


def test_selected_reference_outside_the_session_is_refused() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"selected_reference": "TXN-9001"})
    assert response.status_code == 200
    assert response.json()["kind"] == "handoff"
    assert client.app.state.cases._cases == {} or all(
        c.customer_id == "CUST-0001" for c in client.app.state.cases._cases.values()
    )


def test_selected_reference_must_be_well_formed() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"selected_reference": "has spaces!"})
    assert response.status_code == 422


def test_selected_reference_accepts_non_mock_id_format() -> None:
    """Phase 2 ids are VARCHAR(30) and will not look like 'TXN-1234'.

    The pattern is format-neutral, so a dataset-shaped id passes validation and
    is then resolved (or refused) by the session-scoped lookup, which is the
    real authorization check.
    """
    client = make_customer_client()
    response = client.post(
        "/chat", json={"selected_reference": "01H8ZQ4M2K7PN3RT"}
    )
    assert response.status_code == 200
    # Unknown to this session, so it must not open a case.
    assert response.json()["kind"] == "handoff"
    assert client.app.state.cases._cases == {} or all(
        case.customer_id == "CUST-0001" for case in client.app.state.cases._cases.values()
    )


def test_selected_reference_rejects_path_like_and_overlong_values() -> None:
    client = make_customer_client()
    for bad in ("../../etc/passwd", "TXN 1001", "x" * 65, ""):
        response = client.post("/chat", json={"selected_reference": bad})
        assert response.status_code == 422, bad


def test_chat_confirmation_matches_disputes_service() -> None:
    client = make_customer_client()
    endpoint = client.post(
        "/api/v1/disputes/create",
        json={"transaction_ref": "TXN-1001"},
        headers={"Idempotency-Key": "chat-parity-1"},
    ).json()
    chat = client.post("/chat", json={"message": EXACT}).json()
    assert chat["display"] == endpoint["display"]
    assert chat["messages"] == endpoint["messages"]


def test_stale_charge_chat_returns_handoff() -> None:
    client = make_customer_client()
    response = client.post(
        "/chat",
        json={"message": "I dispute the charge of 2500.00 at ACME Store on 2026-01-15"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "handoff"
    assert body["reason_key"] == "handoffUnverified" or "refused" in body["reason_key"]


def test_refunded_charge_chat_returns_handoff() -> None:
    client = make_customer_client()
    response = client.post(
        "/chat",
        json={"message": "I dispute the charge of 500.00 at ACME Store on 2026-06-05"},
    )
    assert response.status_code == 200
    assert response.json()["kind"] == "handoff"


def test_broken_store_returns_handoff_never_confirmation() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"message": "broken dispute flow error test"})
    assert response.status_code == 200
    assert response.json()["kind"] == "handoff"


def test_agent_request_escalates_on_insistence() -> None:
    client = make_customer_client()
    first = client.post("/chat", json={"message": "I want a human agent"})
    assert first.json()["kind"] == "text"
    second = client.post("/chat", json={"message": "agent please"})
    assert second.json()["kind"] == "handoff"


def test_chat_without_session_401() -> None:
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": "dispute charge 1000"})
    assert response.status_code == 401


def test_chat_extra_field_422() -> None:
    client = make_customer_client()
    response = client.post(
        "/chat", json={"message": EXACT, "customer_id": "CUST-9999"}
    )
    assert response.status_code == 422


def test_chat_rejects_non_customer_role_403() -> None:
    client = TestClient(create_app())
    assert (
        client.post(
            "/auth/login", json={"customer_id": "ADV-0001", "password": "Advisor-001"}
        ).status_code
        == 200
    )
    response = client.post("/chat", json={"message": EXACT})
    assert response.status_code == 403
