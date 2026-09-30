"""Router tests: baseline identity, transports, fixtures, prompted router, PII guard."""

from app.ai.demo import DemoModel
from app.ai.fake import FakeModel


def test_baseline_describe_is_non_empty() -> None:
    for model in (DemoModel(), FakeModel()):
        info = model.describe()
        assert info.model.strip()
        assert info.route.strip()
        assert info.prompt_version.strip()


def test_baseline_understand_carries_zero_cost() -> None:
    result = DemoModel().understand("no reconozco este cargo", [])
    assert result.tokens_in == 0
    assert result.tokens_out == 0
    assert result.cost_usd == 0.0


def test_create_app_injects_fake_model() -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app

    api = TestClient(create_app(model=FakeModel()))
    assert api.app.state.model.describe().model == "fake"
    assert (
        api.post("/session/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code
        == 200
    )
    response = api.post("/chat", json={"message": "no reconozco este cargo"})
    assert response.status_code == 200
    assert response.json()["kind"] in ("clarification", "confirm_box", "handoff", "text")
