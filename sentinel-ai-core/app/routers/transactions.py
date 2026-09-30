"""
GET /api/v1/transactions

Returns the PII-free, candidate-normalized list of dispute-eligible
transactions for the customer identified by the active session.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.session_state import SessionState
from app.services import gold_service

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("", summary="List dispute-eligible transactions for the active session")
async def list_transactions(
    session_id: str = Query(..., description="Active session token"),
    db: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """
    Resolve the ``customer_id`` from the session store, then query the
    PII-free Gold view.  All DuckDB I/O is offloaded via ``asyncio.to_thread``.
    """
    result = await db.execute(
        select(SessionState).where(SessionState.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=401, detail="Session not found or expired.")

    transactions = await gold_service.fetch_transactions_for_customer(session.customer_id)
    return transactions
