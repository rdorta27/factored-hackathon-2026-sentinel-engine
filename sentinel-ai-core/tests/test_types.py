import pytest

from app.orchestrator.types import Candidate, ConversationState, Language, TransactionStatus


def test_candidate_rejects_missing_currency() -> None:
    with pytest.raises(ValueError, match="currency"):
        Candidate(
            candidate_id="c1",
            status=TransactionStatus.APPROVED,
            amount="85.000",
            currency="  ",
            merchant="Exito",
            date="2024-10-01",
            as_of="2024-10-02",
        )


def test_state_has_no_customer_id() -> None:
    state = ConversationState(language=Language.ES_419)
    assert "customer_id" not in state.__dataclass_fields__
