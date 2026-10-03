"""DuckDB Gold adapter: row mapping onto the seam and fallback to the mock."""

from pathlib import Path

import duckdb
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import gold_service
from app.tools.gold import MockGoldStore, to_candidate
from app.tools.gold_duckdb import select_gold, to_gold_row
from app.orchestrator.types import TransactionStatus

AS_OF = "2026-06-17"
_REPO = Path(__file__).resolve().parents[2]
_CORE = _REPO / "sentinel-ai-core"


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


def _hide_default_file(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("SENTINEL_GOLD_DUCKDB", raising=False)
    monkeypatch.setattr(gold_service, "default_gold_duckdb_path", lambda: tmp_path / "absent.duckdb")


def test_missing_view_falls_back_to_the_mock(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "auto")
    _hide_default_file(monkeypatch, tmp_path)
    monkeypatch.setattr(gold_service, "_GOLD_DIR", tmp_path / "nowhere")
    store, source = select_gold(AS_OF)
    assert source == "mock" and isinstance(store, MockGoldStore)


def test_unreadable_view_falls_back_to_the_mock(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "duckdb")
    _hide_default_file(monkeypatch, tmp_path)
    (tmp_path / gold_service._VIEW_TABLE).mkdir()
    monkeypatch.setattr(gold_service, "_GOLD_DIR", tmp_path)
    store, source = select_gold(AS_OF)
    assert source == "mock" and isinstance(store, MockGoldStore)


def test_mock_can_be_forced(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "mock")
    assert select_gold(AS_OF)[1] == "mock"


def test_fraud_score_reaches_the_candidate() -> None:
    row = to_gold_row(view_row(fraud_score=29.4), AS_OF)
    assert to_candidate(row).fraud_score == 29.4
    assert to_candidate(to_gold_row(view_row(fraud_score=None), AS_OF)).fraud_score is None
    assert to_candidate(to_gold_row(view_row(fraud_score=""), AS_OF)).fraud_score is None


def _write_view(path: Path, rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute(
        """
        CREATE TABLE charges (
            transaction_id VARCHAR,
            customer_id VARCHAR,
            amount DOUBLE,
            currency VARCHAR,
            merchant_name VARCHAR,
            transaction_date DATE,
            transaction_status VARCHAR,
            is_disputed BOOLEAN,
            fraud_score DOUBLE
        )
        """
    )
    con.executemany("INSERT INTO charges VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    con.execute(
        f"CREATE VIEW {gold_service._VIEW_TABLE} AS SELECT * FROM charges"
    )
    con.close()


def _charge(reference: str, customer: str, day: str) -> tuple:
    return (reference, customer, 10.0, "MXN", "Tienda", day, "Approved", False, None)


def test_same_source_from_two_folders(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "gold.duckdb"
    _write_view(db, [_charge("T-IN", "C-A", "2026-06-01")])
    monkeypatch.setenv("SENTINEL_GOLD_DUCKDB", str(db))
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "auto")
    monkeypatch.setenv("SENTINEL_STATE_BACKEND", "memory")
    sources = []
    for folder in (_REPO, _CORE):
        monkeypatch.chdir(folder)
        api = TestClient(create_app())
        sources.append(api.get("/api/v1/health").json()["gold_source"])
    assert sources == ["duckdb", "duckdb"]


def test_relative_env_path_ignores_the_launch_folder(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "sentinel-data-engine" / "data" / "gold_bank.duckdb"
    _write_view(db, [_charge("T-IN", "C-A", "2026-06-01")])
    decoy = tmp_path / "launch" / "gold_bank.duckdb"
    _write_view(decoy, [_charge("T-DECOY", "C-A", "2026-06-01")])
    monkeypatch.setattr(gold_service, "repo_root", lambda: tmp_path)
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "auto")
    monkeypatch.setenv("SENTINEL_GOLD_DUCKDB", "sentinel-data-engine/data/gold_bank.duckdb")
    monkeypatch.chdir(tmp_path / "launch")
    assert gold_service.gold_duckdb_path() == db.resolve()
    assert select_gold(AS_OF)[1] == "duckdb"


def test_launch_folder_file_is_not_the_default(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    decoy_dir = tmp_path / "launch"
    decoy_dir.mkdir()
    _write_view(decoy_dir / "data" / "gold_bank.duckdb", [_charge("T-DECOY", "C-A", "2026-06-01")])
    _hide_default_file(monkeypatch, tmp_path)
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "auto")
    monkeypatch.chdir(decoy_dir)
    assert gold_service.gold_duckdb_path() is None
    assert select_gold(AS_OF)[1] == "mock"


def test_mock_reads_no_file_even_when_it_exists(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "gold.duckdb"
    _write_view(db, [_charge("T-IN", "C-A", "2026-06-01")])
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "mock")
    monkeypatch.setenv("SENTINEL_GOLD_DUCKDB", str(db))
    monkeypatch.setenv("SENTINEL_STATE_BACKEND", "memory")

    def boom(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("a file was opened")

    monkeypatch.setattr(gold_service.duckdb, "connect", boom)
    store, source = select_gold(AS_OF)
    assert source == "mock" and isinstance(store, MockGoldStore)
    api = TestClient(create_app())
    assert api.get("/api/v1/health").json()["gold_source"] == "mock"


def test_future_dated_row_is_not_listed_or_selectable(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    db = tmp_path / "gold.duckdb"
    _write_view(
        db,
        [
            _charge("T-IN", "C-A", "2026-06-01"),
            _charge("T-FUTURE", "C-A", "2026-06-18"),
            _charge("T-OTHER", "C-B", "2026-06-01"),
        ],
    )
    monkeypatch.setenv("SENTINEL_GOLD_DUCKDB", str(db))
    monkeypatch.setenv("SENTINEL_GOLD_SOURCE", "duckdb")
    store, source = select_gold(AS_OF)
    assert source == "duckdb"
    listed = store.list_for_customer("C-A")
    assert [row.reference for row in listed] == ["T-IN"]
    assert store.get("T-FUTURE", "C-A") is None
    assert store.get("T-OTHER", "C-A") is None
    assert [row.reference for row in store.list_for_customer("C-B")] == ["T-OTHER"]


def test_fraud_score_stays_out_of_listings_and_replies() -> None:
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code == 200
    listing = api.get("/api/v1/transactions")
    reply = api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    for response in (listing, reply):
        assert response.status_code == 200
        assert "fraud" not in response.text.lower()
