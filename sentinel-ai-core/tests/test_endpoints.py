"""
Integration-style unit tests for /api/v1/transactions and /api/v1/disputes.

Uses an in-memory SQLite database and mocks the Gold DuckDB service so tests
are self-contained and do not require a real Gold data directory.
"""

from __future__ import annotations

import datetime
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_session
from app.main import app
from app.models.session_state import SessionState  # noqa: F401 – registers table


# ---------------------------------------------------------------------------
# In-memory test database
# StaticPool keeps a single shared connection so all sessions see the same data.
# ---------------------------------------------------------------------------

_TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = async_sessionmaker(bind=_TEST_ENGINE, class_=AsyncSession, expire_on_commit=False)


async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSession() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def setup_tables():
    """Create tables once per test session using the in-memory engine."""
    async with _TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _seed_session(customer_id: str = "CUST-001") -> str:
    """Insert a SessionState row, commit, and return its session_id."""
    sid = str(uuid.uuid4())
    async with _TestSession() as db:
        db.add(
            SessionState(
                session_id=sid,
                customer_id=customer_id,
                reference_date=datetime.date.today(),
            )
        )
        await db.commit()
    return sid


_MOCK_TRANSACTIONS = [
    {
        "transaction_id": "TXN-001",
        "transaction_date": "2026-09-01",
        "process_date": "2026-09-02",
        "product_id": "PROD-1",
        "customer_id": "CUST-001",
        "transaction_type": "PURCHASE",
        "amount": 150.00,
        "currency": "USD",
        "channel": "ONLINE",
        "transaction_country": "US",
        "transaction_status": "POSTED",
        "is_fraud": False,
        "fraud_score": 0.1,
        "merchant_name": "Amazon",
        "merchant_category": "RETAIL",
        "customer_segment": "PREMIUM",
        "customer_country": "US",
        "is_disputed": False,
        "days_since_transaction": 29,
        "is_eligible_for_dispute": True,
        "snapshot_date": "2026-09-30",
        "canonical_status": "posted",
        "status_i18n_key": "status.posted",
    }
]


# ---------------------------------------------------------------------------
# /api/v1/transactions tests
# ---------------------------------------------------------------------------


class TestTransactionsEndpoint:
    async def test_returns_401_without_valid_session(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/transactions", params={"session_id": "bad-id"})
        assert resp.status_code == 401

    async def test_returns_transactions_for_valid_session(self, client: AsyncClient) -> None:
        sid = await _seed_session("CUST-001")
        with patch(
            "app.routers.transactions.gold_service.fetch_transactions_for_customer",
            new_callable=AsyncMock,
            return_value=_MOCK_TRANSACTIONS,
        ):
            resp = await client.get("/api/v1/transactions", params={"session_id": sid})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["transaction_id"] == "TXN-001"

    async def test_session_isolation(self, client: AsyncClient) -> None:
        """Two sessions with different customers receive different results."""
        sid_a = await _seed_session("CUST-A")
        sid_b = await _seed_session("CUST-B")

        async def fake_fetch(customer_id: str):
            return [t for t in _MOCK_TRANSACTIONS if t["customer_id"] == customer_id]

        with patch(
            "app.routers.transactions.gold_service.fetch_transactions_for_customer",
            side_effect=fake_fetch,
        ):
            resp_a = await client.get("/api/v1/transactions", params={"session_id": sid_a})
            resp_b = await client.get("/api/v1/transactions", params={"session_id": sid_b})

        # CUST-001 transactions belong to CUST-A's query; CUST-B gets nothing
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        assert len(resp_b.json()) == 0


# ---------------------------------------------------------------------------
# /api/v1/disputes tests
# ---------------------------------------------------------------------------


class TestDisputesEndpoint:
    async def test_list_returns_401_without_valid_session(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/disputes", params={"session_id": "none"})
        assert resp.status_code == 401

    async def test_create_dispute_succeeds(self, client: AsyncClient) -> None:
        sid = await _seed_session("CUST-001")
        with patch(
            "app.routers.disputes.gold_service.fetch_transaction",
            new_callable=AsyncMock,
            return_value=_MOCK_TRANSACTIONS[0],
        ):
            resp = await client.post(
                "/api/v1/disputes",
                json={
                    "session_id": sid,
                    "transaction_id": "TXN-001",
                    "reason": "I did not make this purchase",
                },
            )
        assert resp.status_code == 201
        body = resp.json()
        assert body["transaction_id"] == "TXN-001"
        assert body["status"] == "open"
        assert body["customer_id"] == "CUST-001"

    async def test_create_dispute_rejects_ineligible_transaction(
        self, client: AsyncClient
    ) -> None:
        sid = await _seed_session("CUST-001")
        ineligible = {**_MOCK_TRANSACTIONS[0], "is_eligible_for_dispute": False}
        with patch(
            "app.routers.disputes.gold_service.fetch_transaction",
            new_callable=AsyncMock,
            return_value=ineligible,
        ):
            resp = await client.post(
                "/api/v1/disputes",
                json={
                    "session_id": sid,
                    "transaction_id": "TXN-001",
                    "reason": "Old transaction",
                },
            )
        assert resp.status_code == 422

    async def test_create_dispute_404_when_txn_not_found(self, client: AsyncClient) -> None:
        sid = await _seed_session("CUST-001")
        with patch(
            "app.routers.disputes.gold_service.fetch_transaction",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.post(
                "/api/v1/disputes",
                json={
                    "session_id": sid,
                    "transaction_id": "GHOST-TXN",
                    "reason": "Something wrong",
                },
            )
        assert resp.status_code == 404

    async def test_list_disputes_returns_only_own_cases(self, client: AsyncClient) -> None:
        sid_a = await _seed_session("CUST-A")
        await _seed_session("CUST-B")

        with patch(
            "app.routers.disputes.gold_service.fetch_transaction",
            new_callable=AsyncMock,
            return_value={**_MOCK_TRANSACTIONS[0], "customer_id": "CUST-A"},
        ):
            await client.post(
                "/api/v1/disputes",
                json={"session_id": sid_a, "transaction_id": "TXN-001", "reason": "Test dispute reason"},
            )

        resp = await client.get("/api/v1/disputes", params={"session_id": sid_a})
        assert resp.status_code == 200
        cases = resp.json()
        assert len(cases) == 1
        assert cases[0]["customer_id"] == "CUST-A"
