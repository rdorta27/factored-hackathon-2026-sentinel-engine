from app.orchestrator.types import Candidate, TransactionStatus
from app.tools.fake import InMemoryTools
from app.tools.ports import ToolStatus


def _candidate() -> Candidate:
    return Candidate(
        candidate_id="c1",
        status=TransactionStatus.APPROVED,
        amount="10.00",
        currency="MXN",
        merchant="ACME",
        date="2024-10-01",
        as_of="2024-10-02",
    )


def test_open_dispute_rejects_missing_token() -> None:
    tools = InMemoryTools([_candidate()])
    result = tools.open_dispute("c1", None, "Cargo duplicado", "twice", "k1")
    assert result.status is ToolStatus.REJECTED
    assert tools.by_key == {}


def test_repeated_key_returns_existing_record() -> None:
    tools = InMemoryTools([_candidate()])
    first = tools.open_dispute("c1", "tok", "Cargo duplicado", "twice", "k1")
    second = tools.open_dispute("c1", None, "other", "again", "k1")
    assert first.record is not None
    assert second.record is not None
    assert second.record.dispute_id == first.record.dispute_id
    assert len(tools.by_key) == 1
