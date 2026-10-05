"""Each judge login reaches its demo case, with the file the script generates.

The normal and ambiguous cases share CUST-0001. The high-amount case is
CUST-0002 and the not-me case is CUST-0003. The passwords come from the ignored
sheet, so no plain password is in the repository.
"""

import csv
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "make_judge_users.py"
FIXTURE_PASSWORD = "Testpass-001"


@pytest.fixture()
def judge_logins(tmp_path: Path, monkeypatch) -> dict[str, str]:  # type: ignore[no-untyped-def]
    users = tmp_path / "users.json"
    sheet = tmp_path / "passwords.csv"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--users", str(users), "--passwords", str(sheet)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    rows = list(csv.DictReader(sheet.read_text(encoding="utf-8").splitlines()))
    monkeypatch.setenv("SENTINEL_USERS_PATH", str(users))
    return {row["login"]: row["password"] for row in rows}


def _login(login: str, password: str) -> TestClient:
    api = TestClient(create_app())
    response = api.post("/api/v1/auth/login", json={"login": login, "password": password})
    assert response.status_code == 200, login
    return api


def test_normal_and_ambiguous_cases_share_the_first_customer(judge_logins: dict[str, str]) -> None:
    api = _login("CUST-0001", judge_logins["CUST-0001"])
    assert api.get("/api/v1/auth/me").json()["country"] == "MX"
    api.post("/api/v1/chat", json={"message": "no reconozco este cargo"})
    assert api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"}).json()["kind"] != "handoff"

    api = _login("CUST-0001", judge_logins["CUST-0001"])
    body = api.post("/api/v1/chat", json={"message": "no reconozco un cargo en ACME Store"}).json()
    assert body["kind"] == "clarification"
    assert len(body["candidates"]) >= 2


def test_high_amount_case_is_the_second_customer(judge_logins: dict[str, str]) -> None:
    api = _login("CUST-0002", judge_logins["CUST-0002"])
    assert api.get("/api/v1/auth/me").json()["country"] == "CO"
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    raw = api.post("/api/v1/chat", json={"selected_reference": "TXN-2002"}).json()
    assert raw["kind"] == "handoff"
    assert raw["reason_key"] == "handoff.amountHigh"


def test_not_me_case_is_the_third_customer(judge_logins: dict[str, str]) -> None:
    api = _login("CUST-0003", judge_logins["CUST-0003"])
    assert api.get("/api/v1/auth/me").json()["country"] == "AR"
    api.post("/api/v1/chat", json={"message": "no fui yo, alguien usó mi tarjeta"})
    raw = api.post("/api/v1/chat", json={"selected_reference": "TXN-3003"}).json()
    assert raw["kind"] == "handoff"
    assert "customer_states_not_theirs" in raw["package"]["open_questions"]


def test_documented_fixture_password_does_not_work_with_the_generated_file(judge_logins: dict[str, str]) -> None:
    api = TestClient(create_app())
    response = api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": FIXTURE_PASSWORD})
    assert response.status_code == 401
