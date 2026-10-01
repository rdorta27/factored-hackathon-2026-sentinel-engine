"""
POST /chat

Cookie-session-scoped conversational dispute-intake endpoint for the demo
application.  Drives the orchestrator step function with an in-memory Gold
store and the model from ``app.state.model`` (keyword baseline by default,
no real LLM required).

Per-session state is stored in app.state.memories (InMemoryTools) and
app.state.conversations (ConversationState), both keyed by the session token.
"""

from __future__ import annotations

import secrets
from datetime import date, timedelta
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.observability import Recorder, TurnObserver
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
    selected_reference: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9\-]+$",
    )


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


def _turn_outcome(output: TurnOutput | None) -> str:
    if output is None:
        return "failed"
    if output.kind is OutcomeKind.FAILURE:
        return "rejected" if output.reason == "unknown_candidate" else "failed"
    return "ok"


@router.post("/chat")
def chat(
    body: ChatInput,
    request: Request,
    session: Session = Depends(require_session),
) -> JSONResponse:
    token: str = request.cookies.get(SESSION_COOKIE, "")
    trace_id: str = getattr(request.state, "trace_id", None) or secrets.token_hex(8)

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
    recorder: Recorder = request.app.state.recorder

    observer = TurnObserver(
        recorder=recorder,
        trace_id=trace_id,
        session_ref=recorder.session_ref(token),
        country=session.country,
    )

    bound = SessionBoundLookup(gold, session.customer_id, memory)
    ports = Ports(
        idempotency_scope=token[:12],
        tools=bound,
        model=request.app.state.model,
        country=session.country,
        today=ref_date,
        trace_id=trace_id,
        observer=observer,
    )

    started = perf_counter()
    output: TurnOutput | None = None
    outcome: str | None = None
    policy_rule: str | None = None

    if body.selected_reference is not None:
        # Check if this reference belongs to the customer at all.
        row = gold.get(body.selected_reference, session.customer_id)
        if row is None:
            outcome = "ok"
            policy_rule = "unknownCharge"
            observer.emit(
                step="turn",
                language=state.language.value,
                outcome=outcome,
                attempt=1,
                policy_rule=policy_rule,
                latency_ms=(perf_counter() - started) * 1000,
            )
            return JSONResponse(
                content={
                    "kind": "handoff",
                    "reason_key": "unknownCharge",
                    "reference": f"HO-{trace_id[:8]}",
                    "source": "mock",
                },
                headers={"X-Trace-Id": trace_id},
            )
        # Pre-populate candidates from the Gold store when none are shown yet
        # so that a direct selection (without a prior text turn) is valid.
        if not state.candidates:
            state.candidates = bound.lookup_transactions()
        turn = CandidateIdInput(candidate_id=body.selected_reference)
    else:
        turn = TextInput(text=body.message or "")

    try:
        output = step(turn, state, ports)
    except Exception:
        # Gold or orchestrator failure: degrade gracefully without leaking internals.
        observer.emit(
            step="turn",
            language=state.language.value,
            outcome="failed",
            attempt=1,
            latency_ms=(perf_counter() - started) * 1000,
        )
        return JSONResponse(
            content={"kind": "error", "message_key": "errorGeneric"},
            headers={"X-Trace-Id": trace_id},
        )

    # For FAILURE (unknown/foreign reference), strip candidate details to avoid
    # disclosing data from another customer's transaction.
    if output.kind is OutcomeKind.FAILURE:
        output = TurnOutput(kind=OutcomeKind.FAILURE, language=output.language)

    observer.emit(
        step="turn",
        language=state.language.value,
        outcome=_turn_outcome(output),
        attempt=output.attempt if output.attempt is not None else 1,
        policy_rule=output.reason if output is not None else None,
        latency_ms=(perf_counter() - started) * 1000,
    )

    return JSONResponse(
        content=_to_response(output, ref_date=ref_date),
        headers={"X-Trace-Id": trace_id},
    )
