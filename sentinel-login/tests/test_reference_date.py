"""Reference date comes from SENTINEL_REFERENCE_DATE with a documented default."""

import os
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.disputes.policy import DEFAULT_REFERENCE_DATE, ENV_VAR, reference_date
from app.main import create_app


def test_default_is_the_dataset_end() -> None:
    os.environ.pop(ENV_VAR, None)
    assert DEFAULT_REFERENCE_DATE == "2026-06-17"
    assert reference_date() == date(2026, 6, 17)


def test_environment_override_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "2026-03-01")
    assert reference_date() == date(2026, 3, 1)


def test_invalid_value_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "not-a-date")
    assert reference_date() == date(2026, 6, 17)


def test_app_state_carries_the_reference_date() -> None:
    client = TestClient(create_app())
    assert client.app.state.reference_date == reference_date()


def test_confirmation_reports_the_reference_date() -> None:
    client = TestClient(create_app())
    client.post(
        "/auth/login", json={"customer_id": "CUST-0001", "password": "Testpass-001"}
    )
    body = client.post(
        "/api/v1/disputes/create",
        json={"transaction_ref": "TXN-1001"},
        headers={"Idempotency-Key": "ref-1"},
    ).json()
    assert body["display"]["referenceDate"] == reference_date().isoformat()


def test_sla_is_business_days_from_the_reference_date() -> None:
    client = TestClient(create_app())
    client.post(
        "/auth/login", json={"customer_id": "CUST-0001", "password": "Testpass-001"}
    )
    body = client.post(
        "/api/v1/disputes/create",
        json={"transaction_ref": "TXN-1001"},
        headers={"Idempotency-Key": "ref-2"},
    ).json()
    # 2026-06-17 is a Wednesday; two business days later is Friday the 19th.
    assert body["display"]["slaDate"] == "2026-06-19"
