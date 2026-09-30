from dataclasses import dataclass
from datetime import date
from time import perf_counter
from uuid import uuid4

from app.ai.grounding import extract_facts, ground, rank_candidates
from app.ai.port import ModelPort, UnderstandKind
from app.observability.observer import TurnObserver
from app.orchestrator.types import (
    Candidate,
    CandidateIdInput,
    ConversationState,
    OutcomeKind,
    PendingConfirmation,
    TextInput,
    TurnInput,
    TurnOutput,
)
from app.policy.engine import HitOutcome, Intent, PolicyHit, PolicyRequest, evaluate
from app.policy.load import load_country
from app.tools.ports import ToolStatus, TransactionLookup

MAX_ATTEMPTS = 3
OPEN_ACTION = "open_dispute"


@dataclass
class Ports:
    idempotency_scope: str
    tools: TransactionLookup
    model: ModelPort
    country: str = "MX"
    today: date | None = None
    trace_id: str | None = None
    observer: TurnObserver | None = None


def _emit(ports: Ports, language: str, **fields) -> None:  # type: ignore[no-untyped-def]
    if ports.observer is None:
        return
    ports.observer.emit(language=language, **fields)


def _tool_outcome(status: ToolStatus) -> str:
    return {
        ToolStatus.OK: "ok",
        ToolStatus.REJECTED: "rejected",
        ToolStatus.FAILED: "failed",
        ToolStatus.NOT_FOUND: "failed",
    }[status]


def step(turn: TurnInput, state: ConversationState, ports: Ports) -> TurnOutput:
    if isinstance(turn, CandidateIdInput):
        return _confirm(turn, state, ports)
    return _on_text(turn, state, ports)


def _on_text(turn: TextInput, state: ConversationState, ports: Ports) -> TurnOutput:
    state.turns.append(turn.text)
    if state.pending_confirmation is not None:
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language, text=turn.text)
    started = perf_counter()
    understood = ports.model.understand(turn.text, state.turns)
    _emit(
        ports,
        state.language.value,
        step="understand",
        latency_ms=(perf_counter() - started) * 1000,
    )
    state.language = understood.language
    if understood.kind is UnderstandKind.MISSING:
        state.clarification_count += 1
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language)
    if understood.kind is UnderstandKind.OUT_OF_SCOPE:
        _emit(ports, state.language.value, step="escalate", policy_rule=None)
        return TurnOutput(
            kind=OutcomeKind.HANDOFF,
            language=state.language,
            reason="out_of_scope",
        )
    if understood.kind is UnderstandKind.PERSON:
        state.person_asks += 1
        hit = _hit(state, ports, Intent.PERSON, None)
        return _from_hit(hit, state, None, ports)
    started = perf_counter()
    candidates = ports.tools.lookup_transactions()
    _emit(
        ports,
        state.language.value,
        step="act",
        tool="lookup_transactions",
        latency_ms=(perf_counter() - started) * 1000,
    )
    today = _today(ports)
    facts = extract_facts(turn.text, today.year, [item.merchant for item in candidates])
    result = ground(facts, candidates)
    if result.outcome != "matched" or result.match is None:
        state.clarification_count += 1
        state.candidates = rank_candidates(facts, result.candidates or candidates, today)[:4]
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language)
    state.candidates = candidates
    return _after_policy(state, ports, Intent.CHARGE, result.match, turn.text)


def _confirm(
    turn: CandidateIdInput, state: ConversationState, ports: Ports
) -> TurnOutput:
    pending = state.pending_confirmation
    shown = {item.candidate_id for item in state.candidates}
    if turn.candidate_id not in shown:
        return TurnOutput(kind=OutcomeKind.FAILURE, language=state.language, reason="unknown_candidate")
    selected = shown_candidate(state, turn.candidate_id)
    if pending is None or turn.candidate_id != pending.candidate_id:
        return _after_policy(state, ports, Intent.CHARGE, selected, "")
    hit = _hit(state, ports, Intent.DISPUTE, selected)
    if hit.outcome is not HitOutcome.ALLOW:
        return _from_hit(hit, state, selected, ports)
    token = uuid4().hex
    key = f"{ports.idempotency_scope}:{pending.candidate_id}:{pending.action}"
    started = perf_counter()
    opened = ports.tools.open_dispute(
        pending.candidate_id,
        token,
        pending.category,
        "",
        key,
    )
    _emit(
        ports,
        state.language.value,
        step="act",
        tool="open_dispute",
        outcome=_tool_outcome(opened.status),
        latency_ms=(perf_counter() - started) * 1000,
    )
    if opened.status is not ToolStatus.OK or opened.record is None:
        return _unverified(state, 1, ports)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = perf_counter()
        found = ports.tools.lookup_dispute(opened.record.dispute_id)
        _emit(
            ports,
            state.language.value,
            step="act",
            tool="lookup_dispute",
            outcome="ok" if found is not None else "failed",
            attempt=attempt,
            latency_ms=(perf_counter() - started) * 1000,
        )
        if found is not None:
            state.pending_confirmation = None
            _emit(ports, state.language.value, step="verify")
            return TurnOutput(
                kind=OutcomeKind.CASE_NUMBER,
                language=state.language,
                candidate=selected,
                case_number=found.dispute_id,
                attempt=attempt,
                category=found.category,
            )
        if attempt < MAX_ATTEMPTS:
            started = perf_counter()
            opened = ports.tools.open_dispute(
                pending.candidate_id,
                None,
                pending.category,
                "",
                key,
            )
            _emit(
                ports,
                state.language.value,
                step="act",
                tool="open_dispute",
                outcome=_tool_outcome(opened.status),
                attempt=attempt + 1,
                latency_ms=(perf_counter() - started) * 1000,
            )
    return _unverified(state, MAX_ATTEMPTS, ports)


def _unverified(state: ConversationState, attempt: int, ports: Ports) -> TurnOutput:
    state.pending_confirmation = None
    _emit(ports, state.language.value, step="verify", outcome="failed", attempt=attempt)
    _emit(ports, state.language.value, step="escalate", policy_rule=None, attempt=attempt)
    return TurnOutput(
        kind=OutcomeKind.HANDOFF,
        language=state.language,
        reason="unverified",
        attempt=attempt,
    )


def _hit(
    state: ConversationState,
    ports: Ports,
    intent: Intent,
    candidate: Candidate | None,
) -> PolicyHit:
    policy = load_country(ports.country)
    today = _today(ports)
    started = perf_counter()
    hit = evaluate(
        PolicyRequest(
            intent=intent,
            country=ports.country,
            today=today,
            candidate=candidate,
            clarification_count=state.clarification_count,
            person_asks=state.person_asks,
            policy=policy,
        )
    )
    _emit(
        ports,
        state.language.value,
        step="decide",
        policy_rule=hit.rule_id,
        latency_ms=(perf_counter() - started) * 1000,
    )
    return hit


def _after_policy(
    state: ConversationState,
    ports: Ports,
    intent: Intent,
    selected: Candidate,
    message: str,
) -> TurnOutput:
    hit = _hit(state, ports, intent, selected)
    if hit.outcome is not HitOutcome.ALLOW:
        return _from_hit(hit, state, selected, ports)
    category = ports.model.classify(message)
    state.pending_confirmation = PendingConfirmation(
        candidate_id=selected.candidate_id,
        action=OPEN_ACTION,
        category=category,
    )
    return TurnOutput(
        kind=OutcomeKind.CONFIRM_BOX,
        language=state.language,
        candidate=selected,
        category=category,
        reason=hit.rule_id,
    )


def _from_hit(
    hit: PolicyHit, state: ConversationState, candidate: Candidate | None, ports: Ports
) -> TurnOutput:
    kind = {
        HitOutcome.EXPLAIN: OutcomeKind.EXPLAIN,
        HitOutcome.HANDOFF: OutcomeKind.HANDOFF,
        HitOutcome.OFFER: OutcomeKind.OFFER,
        HitOutcome.ALLOW: OutcomeKind.CONFIRM_BOX,
    }[hit.outcome]
    if kind is OutcomeKind.HANDOFF:
        _emit(ports, state.language.value, step="escalate", policy_rule=hit.rule_id)
    return TurnOutput(
        kind=kind,
        language=state.language,
        candidate=candidate,
        reason=hit.rule_id,
    )


def _today(ports: Ports) -> date:
    if ports.today is not None:
        return ports.today
    policy = load_country(ports.country)
    return policy.demo_today if policy else date(2026, 6, 17)


def shown_candidate(state: ConversationState, candidate_id: str) -> Candidate | None:
    for item in state.candidates:
        if item.candidate_id == candidate_id:
            return item
    return None
