"""DuckDB Gold adapter: row mapping onto the seam and fallback to the mock."""

from app.services import gold_service
from app.tools.gold import MockGoldStore, to_candidate
from app.tools.gold_duckdb import select_gold, to_gold_row
from app.orchestrator.types import TransactionStatus

AS_OF = "2026-06-17"


def view_row(**overrides):  # type: ignore[no-untyped-def]
    row = {
        "transaction_id": "T1",
        "customer_id": "C1",
        "amount": 1234.5,
        "currency": "MXN",
        "merchant_name": "Tienda",
        "transaction_date": "2026-06-01",
        "transaction_status": "Approved",
        "is_disputed": False,
    }
    row.update(overrides)
    return row


def test_view_row_maps_onto_the_seam() -> None:
    row = to_gold_row(view_row(), AS_OF)
    assert (row.reference, row.customer_id, row.amount, row.date, row.as_of) == ("T1", "C1", "1234.50", "2026-06-01", AS_OF)
    assert to_candidate(row).status is TransactionStatus.APPROVED


def test_reversed_and_disputed_flags_carry_over() -> None:
    reversed_row = to_gold_row(view_row(transaction_status="Reversed"), AS_OF)
    assert reversed_row.refunded is True
    assert to_candidate(reversed_row).status is TransactionStatus.REVERSED
    assert to_gold_row(view_row(is_disputed=True), AS_OF).prior_dispute is True


def test_unknown_status_is_not_disputable() -> None:
    assert to_gold_row(view_row(transaction_status="weird"), AS_OF).status == "Pending"


def test_missing_view_falls_back_to_the_mock(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "auto")
    monkeypatch.setattr(gold_service, "_GOLD_DIR", tmp_path / "nowhere")
    store, source = select_gold(AS_OF)
    assert source == "mock" and isinstance(store, MockGoldStore)


def test_unreadable_view_falls_back_to_the_mock(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "duckdb")
    (tmp_path / gold_service._VIEW_TABLE).mkdir()
    monkeypatch.setattr(gold_service, "_GOLD_DIR", tmp_path)
    store, source = select_gold(AS_OF)
    assert source == "mock" and isinstance(store, MockGoldStore)


def test_mock_can_be_forced(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "mock")
    assert select_gold(AS_OF)[1] == "mock"
