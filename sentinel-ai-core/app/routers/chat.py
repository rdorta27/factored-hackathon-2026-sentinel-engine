"""
POST /api/v1/chat

Orchestrates:
  1. Session validation (SQLite lookup)
  2. PII-free fact lookup from Gold DuckDB (asyncio.to_thread)
  3. LLM router invocation (Anthropic Messages API)
  4. Automated reply OR structured HIL HandoffTicket

The LLM is invoked only with PII-free context: transaction amount, merchant
category, date, and eligibility flags.  customer_id is an opaque token.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

from anthropic import AsyncAnthropic
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.session_state import SessionState
from app.schemas.chat import ChatRequest, ChatResponse, HandoffTicket, VerifiedFacts
from app.services import gold_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

_ANTHROPIC_MODEL = os.getenv("SENTINEL_LLM_MODEL", "claude-haiku-4-5-20251001")
_ESCALATION_KEYWORDS = {"agent", "human", "person", "supervisor", "manager", "escalate"}

_SYSTEM_PROMPT = """
You are a banking dispute intake assistant for Sentinel Engine.
Your role is to help customers understand and initiate transaction disputes.
You have access ONLY to PII-free transaction data provided in the user context.
Do NOT speculate about customer names, credit scores, or any information not in the context.
Respond concisely in the locale specified. If the dispute is complex, unclear, or the
customer explicitly requests a human agent, respond with the single word ESCALATE.
""".strip()


def _build_user_context(message: str, transactions: list[dict[str, Any]], locale: str) -> str:
    """Build the user-turn content for the LLM, embedding PII-free facts."""
    txn_summary = "\n".join(
        f"- ID: {t['transaction_id']} | {t.get('transaction_date', 'N/A')} | "
        f"{t.get('amount', 0):.2f} {t.get('currency', '')} | "
        f"Merchant: {t.get('merchant_name', 'N/A')} | "
        f"Status: {t.get('canonical_status', 'N/A')} | "
        f"Eligible: {t.get('is_eligible_for_dispute', False)}"
        for t in transactions[:10]  # cap context size
    )
    return (
        f"[Locale: {locale}]\n"
        f"[Eligible transactions]\n{txn_summary or 'No eligible transactions found.'}\n\n"
        f"Customer message: {message}"
    )


def _pick_escalation_txn(transactions: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the first eligible transaction to anchor the HandoffTicket, if any."""
    eligible = [t for t in transactions if t.get("is_eligible_for_dispute")]
    return eligible[0] if eligible else (transactions[0] if transactions else None)


@router.post("", summary="Send a message to the dispute intake bot")
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_session),
) -> ChatResponse:
    result = await db.execute(
        select(SessionState).where(SessionState.session_id == body.session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=401, detail="Session not found or expired.")

    transactions = await gold_service.fetch_transactions_for_customer(session.customer_id)

    # Keyword-based pre-check for explicit escalation request
    user_lower = body.message.lower()
    explicit_escalation = any(kw in user_lower for kw in _ESCALATION_KEYWORDS)

    llm_reply = "ESCALATE"
    if not explicit_escalation:
        client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        user_content = _build_user_context(body.message, transactions, body.locale)
        try:
            response = await client.messages.create(
                model=_ANTHROPIC_MODEL,
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            llm_reply = response.content[0].text.strip()
        except Exception:
            # On any LLM error, escalate to a human agent
            llm_reply = "ESCALATE"

    should_escalate = llm_reply.upper() == "ESCALATE" or explicit_escalation

    if should_escalate:
        anchor = _pick_escalation_txn(transactions)
        verified = (
            VerifiedFacts(
                transaction_id=anchor["transaction_id"],
                amount=float(anchor.get("amount", 0)),
                currency=anchor.get("currency", ""),
                merchant=anchor.get("merchant_name"),
                transaction_date=str(anchor.get("transaction_date", "")),
                days_since_transaction=int(anchor.get("days_since_transaction", 0)),
                is_eligible_for_dispute=bool(anchor.get("is_eligible_for_dispute", False)),
            )
            if anchor
            else VerifiedFacts(
                transaction_id="N/A",
                amount=0.0,
                currency="",
                merchant=None,
                transaction_date="",
                days_since_transaction=0,
                is_eligible_for_dispute=False,
            )
        )
        # Derive sentinel-login contract fields from the anchor transaction.
        anchor_ref = anchor["transaction_id"] if anchor else "N/A"
        sla_date = (date.today() + timedelta(days=5)).isoformat()

        ticket = HandoffTicket(
            customer_id=session.customer_id,
            verified_facts=verified,
            escalation_reason="Customer requested human agent or dispute complexity exceeded automated handling.",
            claim_summary=body.message[:300],
            # sentinel-login Handoff card fields
            kind="handoff",
            reference=anchor_ref,
            reason_key="handoff.escalated",
            reason_detail="Customer requested human agent or dispute complexity exceeded automated handling.",
            estimated_date=sla_date,
            source="mock",
        )
        return ChatResponse(
            session_id=body.session_id,
            reply="I'm connecting you with a human agent who will assist you shortly.",
            response_type="handoff",
            handoff_ticket=ticket,
        )

    return ChatResponse(
        session_id=body.session_id,
        reply=llm_reply,
        response_type="automated",
    )
