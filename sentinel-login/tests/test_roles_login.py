"""Role-carrying login: each mock role signs in and its session holds the role."""

from fastapi.testclient import TestClient

from app.main import create_app

CREDENTIALS = [
    ("CUST-0001", "Testpass-001", "customer"),
    ("ADV-0001", "Advisor-001", "advisor"),
    ("ADM-0001", "Admin-001", "admin"),
]


def test_each_role_logs_in_with_role_in_response() -> None:
    for customer_id, password, role in CREDENTIALS:
        client = TestClient(create_app())
        response = client.post(
            "/auth/login", json={"customer_id": customer_id, "password": password}
        )
        assert response.status_code == 200
        assert response.json() == {"detail": "Logged in", "role": role}


def test_session_holds_role_for_later_endpoints() -> None:
    client = TestClient(create_app())
    assert (
        client.post(
            "/auth/login", json={"customer_id": "ADV-0001", "password": "Advisor-001"}
        ).status_code
        == 200
    )
    sessions = client.app.state.auth_service._sessions._sessions
    assert len(sessions) == 1
    assert next(iter(sessions.values())).role == "advisor"


def test_roles_do_not_leak_across_users() -> None:
    client = TestClient(create_app())
    client.post("/auth/login", json={"customer_id": "CUST-0001", "password": "Testpass-001"})
    response = client.post(
        "/auth/login", json={"customer_id": "ADM-0001", "password": "Admin-001"}
    )
    assert response.json()["role"] == "admin"
