from dataclasses import dataclass
from datetime import date
from time import perf_counter
from uuid import uuid4

from app.ai.grounding import extract_facts, ground, rank_candidates
from app.ai.port import ModelInfo, ModelPort, UnderstandKind
from app.ai.transport import ModelUnavailable
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
# At most two clarification rounds: the third vague turn hands off (REQ-0001).
MAX_CLARIFICATIONS = 2
# The stored turn window is bounded like the history: the model only reads the
# last few turns, so an unbounded list would grow the session state forever.
MAX_TURNS = 50


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


def _describe(model: ModelPort) -> ModelInfo:
    describe = getattr(model, "describe", None)
    if callable(describe):
        return describe()  # type: ignore[no-any-return]
    return ModelInfo(model="fake", route="mock", prompt_version="none")


def _identity_fields(info: ModelInfo, understood=None) -> dict:  # type: ignore[no-untyped-def]
    return {
        "model": info.model,
        "route": info.route,
        "prompt_version": info.prompt_version,
        "tokens_in": understood.tokens_in if understood is not None else 0,
        "tokens_out": understood.tokens_out if understood is not None else 0,
        "cost_usd": understood.cost_usd if understood is not None else 0.0,
    }


UNDERSTAND_RETRIES = 2


def _digest(state: ConversationState) -> dict:
    """Deterministic system-side context for the model (REQ-0001).

    The last two system question codes plus the shown candidate ids. Codes
    and references only: never customer words, identifiers, or reasoning.
    """
    return {
        "sys_questions": list(state.sys_questions[-2:]),
        "shown_ids": [item.candidate_id for item in state.candidates[:4]],
    }


def _remember_rejected(
    state: ConversationState, candidate_ids: list[str], keep: str | None = None
) -> None:
    for candidate_id in candidate_ids:
        if candidate_id != keep and candidate_id not in state.rejected_ids:
            state.rejected_ids.append(candidate_id)


def _forget_rejected(state: ConversationState, candidate_id: str) -> None:
    if candidate_id in state.rejected_ids:
        state.rejected_ids.remove(candidate_id)


def _record_question(state: ConversationState, code: str) -> None:
    state.sys_questions = [*state.sys_questions, code][-2:]


def _capped(state: ConversationState, ports: Ports) -> TurnOutput | None:
    """Third vague turn: handoff instead of another question (REQ-0001)."""
    if state.clarification_count >= MAX_CLARIFICATIONS:
        _emit(ports, state.language.value, step="escalate", policy_rule="fields.missing")
        return TurnOutput(
            kind=OutcomeKind.HANDOFF,
            language=state.language,
            reason="fields.missing",
        )
    return None


def _model_says_person(message: str, state: ConversationState, ports: Ports) -> bool | None:
    """Ask the model whether this message requests a person.

    Returns True/False, or None when the model is unavailable. The caller
    decides what an unavailable model means; here it never escalates, so a
    failure while the box is open keeps today's behaviour.
    """
    started = perf_counter()
    for _ in range(UNDERSTAND_RETRIES + 1):
        try:
            understood = ports.model.understand(message, state.turns, context=_digest(state))
        except ModelUnavailable:
            continue
        # Same record as the main path, so this call's tokens, cost and latency
        # count in the turn log (REQ-0025, REQ-0055).
        _emit(
            ports,
            state.language.value,
            step="understand",
            latency_ms=(perf_counter() - started) * 1000,
            **_identity_fields(_describe(ports.model), understood),
        )
        return understood.kind is UnderstandKind.PERSON
    _emit(
        ports,
        state.language.value,
        step="understand",
        outcome="failed",
        latency_ms=(perf_counter() - started) * 1000,
        **_identity_fields(_describe(ports.model)),
    )
    return None


def _person_request(state: ConversationState, ports: Ports) -> TurnOutput:
    """One place for the person-request rule (REQ-0040).

    The first ask offers to keep helping; insisting escalates. Used by both
    paths: a plain message and a message that arrives while the confirm box is
    open, so the behaviour cannot drift between them.

    On escalation the pending confirmation is cleared: the customer must not be
    able to confirm and open a case while an advisor is already taking over.
    """
    state.person_asks += 1
    hit = _hit(state, ports, Intent.PERSON, None)
    output = _from_hit(hit, state, None, ports)
    if output.kind is OutcomeKind.HANDOFF:
        state.pending_confirmation = None
    return output


def _on_text(turn: TextInput, state: ConversationState, ports: Ports) -> TurnOutput:
    state.turns.append(turn.text)
    if len(state.turns) > MAX_TURNS:
        del state.turns[: len(state.turns) - MAX_TURNS]
    if state.pending_confirmation is not None:
        # The box swallows everything except a person request. The model is not
        # consulted here for anything else, so a failure cannot change this.
        if _model_says_person(turn.text, state, ports) is True:
            return _person_request(state, ports)
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language, text=turn.text)
    started = perf_counter()
    understood = None
    for _ in range(UNDERSTAND_RETRIES + 1):
        try:
            understood = ports.model.understand(turn.text, state.turns, context=_digest(state))
            break
        except ModelUnavailable:
            continue
    if understood is None:
        _emit(
            ports,
            state.language.value,
            step="understand",
            outcome="failed",
            latency_ms=(perf_counter() - started) * 1000,
            **_identity_fields(_describe(ports.model)),
        )
        _emit(ports, state.language.value, step="escalate", policy_rule="model_unavailable")
        return TurnOutput(
            kind=OutcomeKind.HANDOFF,
            language=state.language,
            reason="model_unavailable",
        )
    info = _describe(ports.model)
    _emit(
        ports,
        state.language.value,
        step="understand",
        latency_ms=(perf_counter() - started) * 1000,
        **_identity_fields(info, understood),
    )
    state.language = understood.language
    offered_scope = state.scope_asks > 0
    if understood.kind is not UnderstandKind.OUT_OF_SCOPE:
        state.scope_asks = 0
    if understood.not_mine:
        state.states_not_theirs = True
    if understood.kind is UnderstandKind.MISSING:
        capped = _capped(state, ports)
        if capped is not None:
            return capped
        state.clarification_count += 1
        _record_question(state, "missing")
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language)
    if understood.kind is UnderstandKind.OUT_OF_SCOPE:
        # Decision 008: say what is out of scope and offer the advisor; a model
        # error on the first turn costs one sentence, not a ticket. A second
        # out-of-scope turn in a row hands off.
        state.scope_asks += 1
        if state.scope_asks == 1:
            _emit(ports, state.language.value, step="decide", policy_rule="out_of_scope.ask")
            return TurnOutput(kind=OutcomeKind.OFFER, language=state.language, reason="out_of_scope.ask")
        _emit(ports, state.language.value, step="escalate", policy_rule=None)
        return TurnOutput(
            kind=OutcomeKind.HANDOFF,
            language=state.language,
            reason="out_of_scope",
        )
    if understood.kind is UnderstandKind.PERSON:
        if offered_scope:
            # Answering the out-of-scope offer with "an advisor" is the second ask.
            state.person_asks = max(state.person_asks, 1)
        return _person_request(state, ports)
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
        capped = _capped(state, ports)
        if capped is not None:
            return capped
        state.clarification_count += 1
        _record_question(state, "which_charge")
        if understood.not_mine:
            # The customer denied what was shown: never show it again.
            _remember_rejected(state, [item.candidate_id for item in state.candidates])
        ranked = rank_candidates(facts, result.candidates or candidates, today)
        state.candidates = [
            item for item in ranked if item.candidate_id not in state.rejected_ids
        ][:4]
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language)
    # Repair: new facts re-anchor to this charge; any previously shown charge
    # that is not the match is superseded and joins the rejected list.
    _remember_rejected(
        state,
        [item.candidate_id for item in state.candidates],
        keep=result.match.candidate_id,
    )
    _forget_rejected(state, result.match.candidate_id)
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
    # Pressing the button is the customer choosing the charge, not asking for a
    # person: an unanswered offer to help must not decide this turn. Clearing it
    # here keeps the policy rule from firing on a confirmation (REQ-0040).
    state.person_asks = 0
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
            states_not_theirs=state.states_not_theirs,
            policy=policy,
        )
    )
    _emit(
        ports,
        state.language.value,
        step="decide",
        policy_rule=hit.rule_id,
        latency_ms=(perf_counter() - started) * 1000,
        policy_version=None if policy is None else policy.version,
        policy_synthetic=None if policy is None else policy.synthetic,
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
