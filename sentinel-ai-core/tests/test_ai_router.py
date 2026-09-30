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
