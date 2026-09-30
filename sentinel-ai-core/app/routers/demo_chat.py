"""
POST /chat

Cookie-session-scoped conversational dispute-intake endpoint for the demo
application.  Drives the orchestrator step function with an in-memory Gold
store and the DemoModel (no real LLM required).

Per-session state is stored in app.state.memories (InMemoryTools) and
app.state.conversations (ConversationState), both keyed by the session token.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from app.ai.demo import DemoModel
from app.orchestrator.step import Ports, step
from app.orchestrator.types import (
    CandidateIdInput,
    ConversationState,
    Language,
    OutcomeKind,
    TextInput,
    TurnOutput,
)
from app.session.models import Session
from app.session.router import SESSION_COOKIE, require_session
from app.tools.bound import SessionBoundLookup
from app.tools.fake import InMemoryTools

router = APIRouter(tags=["chat"])

_MODEL = DemoModel()

_KIND_MAP = {
    OutcomeKind.QUESTION: "clarification",
    OutcomeKind.EXPLAIN: "text",
    OutcomeKind.OFFER: "text",
    OutcomeKind.CONFIRM_BOX: "confirm_box",
    OutcomeKind.CASE_NUMBER: "case_confirmation",
    OutcomeKind.HANDOFF: "handoff",
    OutcomeKind.FAILURE: "handoff",
}


class ChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str | None = None
    selected_reference: str | None = None


def _sla_date(ref_date: date) -> str:
    """Return a 5-calendar-day SLA estimate from the reference date."""
    return (ref_date + timedelta(days=5)).isoformat()


def _to_response(output: TurnOutput, ref_date: date | None = None) -> dict[str, Any]:
    kind = _KIND_MAP.get(output.kind, output.kind.value)
    result: dict[str, Any] = {"kind": kind}

    if output.candidate is not None:
        candidate_dict = {
            "reference": output.candidate.candidate_id,
            "merchant": output.candidate.merchant,
            "amount": output.candidate.amount,
            "currency": output.candidate.currency,
            "date": output.candidate.date,
        }
        result["candidate"] = candidate_dict
        # Also expose as "transaction" for tests that use that key.
        result["transaction"] = candidate_dict

    if output.kind is OutcomeKind.CASE_NUMBER:
        result["verified"] = True
        result["source"] = "mock"
        result["case_id"] = output.case_number

    if output.attempt is not None:
        result["attempt"] = output.attempt

    if output.reason:
        result["reason"] = output.reason

    # Enrich handoff responses with the sentinel-login Handoff card contract so
    # the frontend can render the i18n escalation card without changes.
    if kind == "handoff":
        candidate = output.candidate
        result["reference"] = (
            candidate.candidate_id if candidate is not None else "HO-pending"
        )
        rule = output.reason or "escalated"
        result["reason_key"] = f"handoff.{rule}"
        result["reason_detail"] = (
            f"Escalation triggered by rule: {rule}. "
            "A human advisor will review your case."
        )
        result["estimated_date"] = _sla_date(ref_date) if ref_date else None
        result["source"] = "mock"

    return result


@router.post("/chat")
def chat(
    body: ChatInput,
    request: Request,
    session: Session = Depends(require_session),
) -> dict[str, Any]:
    token: str = request.cookies.get(SESSION_COOKIE, "")

    memories: dict[str, InMemoryTools] = request.app.state.memories
    conversations: dict[str, ConversationState] = request.app.state.conversations

    if token not in memories:
        memories[token] = InMemoryTools()
    if token not in conversations:
        conversations[token] = ConversationState(language=Language.ES_419)

    memory = memories[token]
    state = conversations[token]
    gold = request.app.state.gold
    ref_date = request.app.state.reference_date

    bound = SessionBoundLookup(gold, session.customer_id, memory)
    ports = Ports(
        session_ref=token,
        tools=bound,
        model=_MODEL,
        country=session.country,
        today=ref_date,
    )

    if body.selected_reference is not None:
        # Pre-populate candidates from the Gold store when none are shown yet
        # so that a direct selection (without a prior text turn) is valid.
        if not state.candidates:
            state.candidates = bound.lookup_transactions()
        turn = CandidateIdInput(candidate_id=body.selected_reference)
    else:
        turn = TextInput(text=body.message or "")

    output = step(turn, state, ports)

    # For FAILURE (unknown/foreign reference), strip candidate details to avoid
    # disclosing data from another customer's transaction.
    if output.kind is OutcomeKind.FAILURE:
        output = TurnOutput(kind=OutcomeKind.FAILURE, language=output.language)

    return _to_response(output, ref_date=ref_date)
