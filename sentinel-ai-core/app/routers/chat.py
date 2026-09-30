from datetime import datetime, timezone
from time import perf_counter

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.ai.demo import DemoModel
from app.observability import Recorder, TurnObserver
from app.orchestrator.step import Ports, step
from app.orchestrator.types import (
    Candidate,
    CandidateIdInput,
    ConversationState,
    Language,
    OutcomeKind,
    TextInput,
    TurnOutput,
)
from app.session.models import Session
from app.session.router import require_session
from app.tools.bound import SessionBoundLookup
from app.tools.fake import InMemoryTools
from app.tools.gold import GoldTransactions, to_candidate

router = APIRouter(prefix="/chat", tags=["chat"])
_MODEL = DemoModel()


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(default="", max_length=2000)
    selected_reference: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$",
    )


def _trace(request: Request) -> str:
    return getattr(request.state, "trace_id", "unknown")


def _bundle(request: Request, session: Session) -> tuple[ConversationState, SessionBoundLookup]:
    states: dict = request.app.state.conversations
    memories: dict = request.app.state.memories
    if session.token not in states:
        states[session.token] = ConversationState(language=Language.ES_419)
        memories[session.token] = InMemoryTools()
    gold: GoldTransactions = request.app.state.gold
    tools = SessionBoundLookup(gold, session.customer_id, memories[session.token])
    return states[session.token], tools


def _ports(
    request: Request, session: Session, tools: SessionBoundLookup, observer: TurnObserver
) -> Ports:
    return Ports(
        session_ref=session.token[:12],
        tools=tools,
        model=_MODEL,
        country=session.country,
        today=request.app.state.reference_date,
        trace_id=_trace(request),
        observer=observer,
    )


def _turn_outcome(output: TurnOutput | None) -> str:
    if output is None:
        return "failed"
    if output.kind is OutcomeKind.FAILURE:
        return "rejected" if output.reason == "unknown_candidate" else "failed"
    return "ok"


def _close_turn(
    request: Request,
    observer: TurnObserver,
    state: ConversationState,
    output: TurnOutput | None,
    latency_ms: float,
    outcome: str | None = None,
    reason: str | None = None,
) -> None:
    observer.emit(
        step="turn",
        language=state.language.value,
        outcome=outcome if outcome is not None else _turn_outcome(output),
        attempt=output.attempt if output is not None and output.attempt is not None else 1,
        policy_rule=reason if reason is not None else (output.reason if output is not None else None),
        latency_ms=latency_ms,
    )


def _ineligible_key(candidate: Candidate, today) -> str | None:
    if candidate.is_disputed:
        return "candidateDisputed"
    if candidate.status.value == "Reversed":
        return "candidateReversed"
    if candidate.status.value == "Declined":
        return "candidateDeclined"
    if candidate.status.value == "Pending":
        return "candidatePending"
    if candidate.status.value != "Approved":
        return "candidateOutOfWindow"
    age = (today - datetime.fromisoformat(candidate.date).date()).days
    if age > 90:
        return "candidateOutOfWindow"
    return None


def _candidate_payload(candidate: Candidate, today) -> dict:
    reason = _ineligible_key(candidate, today)
    return {
        "reference": candidate.candidate_id,
        "amount": candidate.amount,
        "currency": candidate.currency,
        "merchant": candidate.merchant,
        "date": candidate.date,
        "eligible": reason is None,
        "ineligibleKey": reason,
    }


def _render(output, state: ConversationState, request: Request) -> dict:
    today = request.app.state.reference_date
    kind = output.kind
    if kind is OutcomeKind.QUESTION:
        return {
            "kind": "clarification",
            "message_key": "clarifyAmbiguous",
            "missing": "transaction",
            "candidates": [_candidate_payload(item, today) for item in state.candidates],
        }
    if kind is OutcomeKind.CONFIRM_BOX and output.candidate is not None:
        item = output.candidate
        return {
            "kind": "confirm_box",
            "message_key": "confirmCharge",
            "candidate": {
                "reference": item.candidate_id,
                "amount": item.amount,
                "currency": item.currency,
                "merchant": item.merchant,
                "date": item.date,
            },
        }
    if kind is OutcomeKind.CASE_NUMBER:
        facts = output.candidate
        return {
            "kind": "case_confirmation",
            "case_id": output.case_number,
            "transaction": {
                "amount": facts.amount if facts else "",
                "currency": facts.currency if facts else "",
                "merchant": facts.merchant if facts else "",
                "date": facts.date if facts else "",
            },
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verified": True,
            "display": {
                "referenceDate": today.isoformat(),
                "amount": facts.amount if facts else "",
                "currency": facts.currency if facts else "",
                "merchant": facts.merchant if facts else "",
            },
            "messages": {
                "rule": output.reason or "status.approved",
                "noFunds": "noFundsHeld",
                "nextStep": "nextStepAdvisorReview",
            },
            "source": "mock",
        }
    if kind is OutcomeKind.HANDOFF:
        body = {
            "kind": "handoff",
            "reason_key": output.reason or "handoff",
            "reference": f"HO-{_trace(request)}",
            "source": "mock",
        }
        if output.attempt is not None:
            body["attempt"] = output.attempt
        return body
    if kind is OutcomeKind.FAILURE:
        return {"kind": "error", "message_key": "errorGeneric", "trace_id": _trace(request)}
    return {"kind": "text", "message_key": output.reason or "offerHelp"}


@router.post("")
def chat(
    body: ChatRequest,
    request: Request,
    session: Session = Depends(require_session),
) -> JSONResponse:
    state, tools = _bundle(request, session)
    recorder: Recorder = request.app.state.recorder
    observer = TurnObserver(
        recorder=recorder,
        trace_id=_trace(request),
        session_ref=recorder.session_ref(session.token),
        country=session.country,
    )
    ports = _ports(request, session, tools, observer)
    started = perf_counter()
    try:
        if body.selected_reference:
            gold: GoldTransactions = request.app.state.gold
            row = gold.get(body.selected_reference, session.customer_id)
            if row is None:
                payload = {
                    "kind": "handoff",
                    "reason_key": "unknownCharge",
                    "reference": f"HO-{_trace(request)}",
                    "source": "mock",
                }
                _close_turn(
                    request,
                    observer,
                    state,
                    None,
                    (perf_counter() - started) * 1000,
                    outcome="ok",
                    reason="unknownCharge",
                )
                return JSONResponse(status_code=status.HTTP_200_OK, content=payload)
            candidate = to_candidate(row)
            if all(item.candidate_id != candidate.candidate_id for item in state.candidates):
                state.candidates.append(candidate)
            output = step(CandidateIdInput(body.selected_reference), state, ports)
        else:
            output = step(TextInput(body.message), state, ports)
    except Exception:
        _close_turn(request, observer, state, None, (perf_counter() - started) * 1000)
        payload = {"kind": "error", "message_key": "errorGeneric", "trace_id": _trace(request)}
        return JSONResponse(status_code=status.HTTP_200_OK, content=payload)
    _close_turn(request, observer, state, output, (perf_counter() - started) * 1000)
    return JSONResponse(status_code=status.HTTP_200_OK, content=_render(output, state, request))
