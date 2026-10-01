"""
POST /api/v1/disputes   – open a new dispute case
GET  /api/v1/disputes   – list all cases for the active session's customer
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.dispute_case import DisputeCase
from app.models.session_state import SessionState
from app.schemas.disputes import DisputeCreateRequest, DisputeResponse
from app.services import gold_service

router = APIRouter(prefix="/api/v1/disputes", tags=["disputes"])


async def _resolve_session(session_id: str, db: AsyncSession) -> SessionState:
    """Return SessionState or raise 401."""
    result = await db.execute(
        select(SessionState).where(SessionState.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=401, detail="Session not found or expired.")
    return session


@router.post("", status_code=201, summary="Open a new dispute case")
async def create_dispute(
    body: DisputeCreateRequest,
    db: AsyncSession = Depends(get_session),
) -> DisputeResponse:
    """
    1. Validate the session.
    2. Fetch the transaction from the PII-free Gold view (session-scoped).
    3. Persist the dispute record in SQLite.
    """
    session = await _resolve_session(body.session_id, db)

    txn = await gold_service.fetch_transaction(session.customer_id, body.transaction_id)
    if txn is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found or not eligible for dispute.",
        )
    if not txn.get("is_eligible_for_dispute", False):
        raise HTTPException(
            status_code=422,
            detail="Transaction is not eligible for dispute (already disputed or > 90 days old).",
        )

    dispute = DisputeCase(
        dispute_id=str(uuid.uuid4()),
        customer_id=session.customer_id,
        transaction_id=body.transaction_id,
        amount=float(txn.get("amount", 0)),
        merchant=txn.get("merchant_name"),
        status="open",
    )
    db.add(dispute)
    await db.commit()
    await db.refresh(dispute)
    return DisputeResponse.model_validate(dispute)


@router.get("", summary="List dispute cases for the active session")
async def list_disputes(
    session_id: str = Query(..., description="Active session token"),
    db: AsyncSession = Depends(get_session),
) -> list[DisputeResponse]:
    """Return all dispute cases owned by the session's customer."""
    session = await _resolve_session(session_id, db)
    result = await db.execute(
        select(DisputeCase)
        .where(DisputeCase.customer_id == session.customer_id)
        .order_by(DisputeCase.created_at.desc())
    )
    cases = result.scalars().all()
    return [DisputeResponse.model_validate(c) for c in cases]
