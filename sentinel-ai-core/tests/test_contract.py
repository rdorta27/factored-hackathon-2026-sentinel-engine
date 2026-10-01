"""Canonical API contract: one app, `/api/v1` only, every reply typed (spec `chat`)."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import create_app
from app.schemas.chat import (
    CaseConfirmation,
    Clarification,
    ConfirmBox,
    ErrorReply,
    Handoff,
    TextReply,
    TransactionList,
)

PASSWORD = "Testpass-001"
I18N = Path(__file__).resolve().parents[1] / "app" / "static" / "i18n"
LOCALES = {name: json.loads((I18N / f"{name}.json").read_text(encoding="utf-8")) for name in ("es-419", "pt-BR")}


def logged_in(model=None) -> TestClient:  # type: ignore[no-untyped-def]
    api = TestClient(create_app(model=model))
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code == 200
    return api


def chat(api: TestClient, **body: str) -> dict:
    response = api.post("/api/v1/chat", json=body)
    assert response.status_code == 200
    return response.json()


def parsed(model: type[BaseModel], body: dict) -> BaseModel:
    """The reply validates against its strict model (extra fields are rejected)."""
    return model.model_validate(body)


def assert_translated(*keys: str | None) -> None:
    for key in keys:
        if key is None:
            continue
        for name, strings in LOCALES.items():
            assert key in strings, f"{key} missing in {name}"


def test_served_app_is_the_full_app() -> None:
    from app.main import app

    api = TestClient(app)
    assert api.get("/ui/").status_code == 200
    assert api.get("/api/v1/health").json()["status"] == "ok"
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code == 200
    assert api.get("/api/v1/transactions").status_code == 200
    assert api.post("/api/v1/chat", json={"message": "hola"}).status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/chat"),
        ("get", "/transactions"),
        ("post", "/session/login"),
        ("post", "/auth/login"),
        ("post", "/api/v1/session/login"),
        ("get", "/api/v1/session/me"),
        ("get", "/health"),
    ],
)
def test_old_paths_are_gone(method: str, path: str) -> None:
    api = TestClient(create_app())
    assert getattr(api, method)(path).status_code in (404, 405)


def test_listing_matches_the_contract() -> None:
    listing = parsed(TransactionList, logged_in().get("/api/v1/transactions").json())
    by_ref = {row.reference: row for row in listing.transactions}
    assert by_ref["TXN-1006"].eligible is True
    assert by_ref["TXN-1002"].ineligibleKey == "candidateOutOfWindow"
    assert by_ref["TXN-1003"].ineligibleKey == "candidateReversed"
    assert by_ref["TXN-1004"].ineligibleKey == "candidateDisputed"
    assert_translated(*(row.ineligibleKey for row in listing.transactions))


def test_me_never_returns_the_customer_id() -> None:
    assert logged_in().get("/api/v1/auth/me").json() == {"role": "customer", "country": "MX"}


def test_normal_case_variants_match_the_contract() -> None:
    api = logged_in()
    question = parsed(Clarification, chat(api, message="hola"))
    assert question.candidates, "a clarification offers the customer's charges"
    assert_translated(question.message_key)

    box = parsed(ConfirmBox, chat(api, selected_reference="TXN-1006"))
    assert box.candidate.merchant == "Cafe Central"
    assert_translated(box.message_key)

    case = parsed(CaseConfirmation, chat(api, selected_reference="TXN-1006"))
    assert case.verified is True and case.source == "mock"
    assert case.display.referenceDate == "2026-06-17"
    assert_translated(case.messages.nextStep, case.messages.rule, case.messages.noFunds)


def test_person_request_offers_then_hands_off_with_a_package() -> None:
    api = logged_in()
    offer = parsed(TextReply, chat(api, message="quiero una persona"))
    assert_translated(offer.message_key)

    raw = chat(api, message="quiero una persona")
    handoff = parsed(Handoff, raw)
    assert_translated(handoff.reason_key)
    package = handoff.package
    assert package.request == "person"
    assert package.language == "es-419" and package.country == "MX"
    assert package.open_questions == ["customer_requested_person"]
    assert any(action.step == "escalate" for action in package.actions_taken)
    assert "CUST-" not in json.dumps(raw)
    assert "quiero una persona" not in json.dumps(raw), "no raw transcript in the package"


def test_handoff_package_is_logged_on_the_turn_record() -> None:
    api = logged_in()
    chat(api, message="quiero una persona")
    response = api.post("/api/v1/chat", json={"message": "quiero una persona"})
    trace_id = response.headers["X-Trace-Id"]
    turn = [r for r in api.app.state.recorder.records_for(trace_id) if r.step == "turn"]
    assert turn and turn[-1].handoff == response.json()["package"]


def test_foreign_reference_is_a_handoff_without_disclosure() -> None:
    raw = chat(logged_in(), selected_reference="TXN-9001")
    handoff = parsed(Handoff, raw)
    assert handoff.reason_key == "unknownCharge"
    assert handoff.package.verified_facts is None
    assert "ACME Store" not in json.dumps(raw) and "100.00" not in json.dumps(raw)


def test_pipeline_failure_is_a_generic_error_with_trace() -> None:
    class BrokenModel:
        def understand(self, message, turns):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

        def classify(self, message):  # type: ignore[no-untyped-def]
            return "unrecognized"

    error = parsed(ErrorReply, chat(logged_in(model=BrokenModel()), message="hola"))
    assert error.message_key == "errorGeneric"
    assert len(error.trace_id) == 16
