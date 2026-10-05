import re
from dataclasses import dataclass
from datetime import date
from time import perf_counter, time
from uuid import uuid4

from app.ai.drafts import DraftFacts, fill_draft, validate_draft
from app.ai.grounding import narrow, normalize_text
from app.ai.guard import is_injection, refuse_extraction
from app.ai.port import (
    SUBTYPE_OUT_OF_SCOPE,
    ModelInfo,
    ModelPort,
    UnderstandKind,
    UnderstandResult,
)
from app.ai.transport import ModelUnavailable
from app.observability.observer import TurnObserver
from app.orchestrator.explanation import asks_why, explanation_for, is_why_followup
from app.orchestrator.types import (
    Candidate,
    CandidateIdInput,
    ConversationState,
    Language,
    LastDecision,
    OutcomeKind,
    PendingConfirmation,
    TextInput,
    TurnInput,
    TurnOutput,
)
from app.policy.engine import (
    EXPLAINABLE_RULES,
    HitOutcome,
    Intent,
    PolicyHit,
    PolicyRequest,
    _expired,
    decision_snapshot,
    evaluate,
)
from app.policy.load import load_country
from app.tools.bound import GoldTimeout
from app.tools.ports import ToolStatus, TransactionLookup

MAX_ATTEMPTS = 3
OPEN_ACTION = "open_dispute"
# A pending confirm box expires five minutes after it opened (REQ-0005).
# A late confirmation never writes; the loop shows the candidate again.
CONFIRM_TTL_S = 300.0
# At most two clarification rounds: the third vague turn hands off (REQ-0001).
MAX_CLARIFICATIONS = 2
# The stored turn window is bounded like the history: the model only reads the
# last few turns, so an unbounded list would grow the session state forever.
MAX_TURNS = 50

# The words table (design 5). A turn that does not decide may show the model
# draft; a turn that decides uses templates only.
DRAFT_ALLOWED_KINDS = frozenset(
    {OutcomeKind.EXPLAIN, OutcomeKind.OFFER, OutcomeKind.QUESTION}
)
TEMPLATE_ONLY_KINDS = frozenset(
    {OutcomeKind.CONFIRM_BOX, OutcomeKind.CASE_NUMBER, OutcomeKind.HANDOFF, OutcomeKind.FAILURE}
)

# Opener subtypes (contract v3): small talk that never hands off. "unclear" is
# not an opener: it still asks a clarifying question.
OPENER_SUBTYPES = ("greeting", "thanks", "goodbye", "identity", "help")
# Opener patterns are the fallback for v2 and the baseline (no subtype). They
# run only on a `missing` result and only on a short message.
OPENER_MAX_WORDS = 8
_OPENER_PATTERNS = (
    ("greeting", re.compile(
        r"^(hola|buen[oa]s?\s+(d[ií]as|tardes|noches)|ol[aá]|oi|bom dia|boa tarde|boa noite|hey|hi)\b"
    )),
    ("thanks", re.compile(r"\b(gracias|muchas gracias|mil gracias|obrigad[oa]|valeu|agradecido)\b")),
    ("goodbye", re.compile(r"\b(adi[oó]s|chau|hasta luego|hasta pronto|at[ée] logo|tchau|adeus)\b")),
    ("identity", re.compile(
        r"\b(eres un bot|es un bot|eres un robot|sos un bot|eres una persona|es una persona|"
        r"eres humano|es humano|voc[êe] [eé] um (bot|rob[oô])|rob[oô]|um bot)\b"
    )),
    ("help", re.compile(
        r"\b(en qu[ée] (puedo|te puedo|puedes) ayudar|qu[ée] puedes hacer|para qu[ée] sirves|"
        r"c[oó]mo funcionas|como funciona|ajuda|em que (posso|pode) ajudar|o que voc[êe] faz)\b"
    )),
)
# A charge noun marks a request even when the router reads the message as
# `missing`: a greeting plus a request keeps the request.
_CHARGE_NOUNS = (
    "cargo", "cargos", "cobro", "cobros", "cobranca", "cobrança", "compra", "compras",
    "consumo", "movimiento", "movimientos", "transaccion", "transacción", "reclamo",
    "disputa", "contestacao", "contestação",
)


def _looks_like_request(text: str) -> bool:
    normalized = normalize_text(text)
    return any(noun in normalized for noun in _CHARGE_NOUNS)


def _opener_subtype(text: str, understood: UnderstandResult) -> str | None:
    """The opener subtype, or None. Never hides a charge request."""
    if _looks_like_request(text):
        return None
    if understood.subtype in OPENER_SUBTYPES:
        return understood.subtype
    if understood.subtype is not None:
        return None
    if len(text.split()) > OPENER_MAX_WORDS:
        return None
    normalized = normalize_text(text)
    for subtype, pattern in _OPENER_PATTERNS:
        if pattern.search(normalized):
            return subtype
    return None


def _variant_key(base: str, turn_count: int) -> str:
    """One of two reviewed templates, chosen by turn count (design 6)."""
    return base if turn_count % 2 == 0 else f"{base}.1"


def _draft_text(
    understood: UnderstandResult | None,
    facts: DraftFacts,
    state: ConversationState,
    ports: "Ports",
) -> str:
    """The validated model words for this turn, or "" for the template.

    A rejected draft falls back to the template and the turn record names the
    reason (spec chat, decision 024).
    """
    if understood is None or not understood.reply_draft:
        return ""
    accepted, reason = validate_draft(understood.reply_draft, facts, state.language.value)
    if accepted:
        return fill_draft(understood.reply_draft, facts)
    _emit(
        ports,
        state.language.value,
        step="understand",
        event=f"draft_rejected:{reason}",
    )
    return ""


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


def _lookup_transactions(state: ConversationState, ports: Ports) -> list[Candidate] | TurnOutput:
    """Gold reads under the time budget. Three timeouts hand off with no case number."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = perf_counter()
        try:
            rows = ports.tools.lookup_transactions()
        except GoldTimeout:
            _emit(
                ports,
                state.language.value,
                step="act",
                tool="lookup_transactions",
                outcome="timeout",
                attempt=attempt,
                latency_ms=(perf_counter() - started) * 1000,
            )
            continue
        _emit(
            ports,
            state.language.value,
            step="act",
            tool="lookup_transactions",
            attempt=attempt,
            latency_ms=(perf_counter() - started) * 1000,
        )
        return rows
    _emit(ports, state.language.value, step="escalate", policy_rule=None, attempt=MAX_ATTEMPTS)
    return TurnOutput(
        kind=OutcomeKind.HANDOFF,
        language=state.language,
        reason="unverified",
        attempt=MAX_ATTEMPTS,
    )


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
        "label": understood.kind.value if understood is not None else None,
        "confidence": understood.confidence if understood is not None else None,
    }


_PT_MARKS = ("não", "nao", "palavra", "instruções", "instrucoes", "você", "voce", "seu prompt", "cobrança")


def _message_language(text: str, default: Language) -> Language:
    lowered = text.lower()
    if any(mark in lowered for mark in _PT_MARKS):
        return Language.PT_BR
    return default


def _extraction_refusal(state: ConversationState, ports: Ports) -> TurnOutput:
    """Out-of-scope offer with its own key. The third in a row hands off."""
    state.scope_asks += 1
    if state.scope_asks <= MAX_SCOPE_OFFERS:
        _emit(ports, state.language.value, step="decide", policy_rule="extraction_refused")
        return TurnOutput(
            kind=OutcomeKind.OFFER,
            language=state.language,
            reason="extraction.refused",
        )
    _emit(ports, state.language.value, step="escalate", policy_rule="extraction_refused")
    return TurnOutput(kind=OutcomeKind.HANDOFF, language=state.language, reason="out_of_scope")


UNDERSTAND_RETRIES = 2
# Out-of-scope turns in a row that are answered with the offer; the next one hands off.
MAX_SCOPE_OFFERS = 2


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


def _explanation(state: ConversationState, ports: Ports) -> TurnOutput:
    """Answer a why follow-up from the stored decision, never recomputing it."""
    mapped = explanation_for(state.last_decision)
    _emit(
        ports,
        state.language.value,
        step="decide",
        policy_rule=mapped.rule_id or mapped.message_key,
    )
    return TurnOutput(
        kind=OutcomeKind.EXPLANATION,
        language=state.language,
        reason=mapped.rule_id,
        explanation_key=mapped.message_key,
        explanation_values=mapped.values,
    )


# A dispute-status question combines a case word with a status word. It is a
# deterministic check in code, like the extraction refusal, so it runs before
# the model and never opens a case (REQ-0003, REQ-0006).
_STATUS_MARKERS = (
    "ya abri", "ya abrí", "en que va", "en qué va", "estado de", "estado del",
    "estado da", "status", "andamento", "como va", "cómo va", "como está",
    "como esta", "já abri", "ja abri",
)
_CASE_WORDS = (
    "disputa", "reclamo", "caso", "contestação", "contestacao", "reclamação",
    "reclamacao", "disputas", "reclamos", "casos",
)


def _is_dispute_status_question(text: str) -> bool:
    lowered = text.lower()
    has_marker = any(marker in lowered for marker in _STATUS_MARKERS)
    has_case = any(word in lowered for word in _CASE_WORDS)
    return has_marker and has_case


def _dispute_status(state: ConversationState, ports: Ports) -> TurnOutput:
    """Answer a dispute-status question from the case store. Never opens a case."""
    find = getattr(ports.tools, "disputes", None)
    rows = find() if callable(find) else []
    if not rows:
        _emit(ports, state.language.value, step="decide", policy_rule="dispute.status.none")
        return TurnOutput(
            kind=OutcomeKind.EXPLANATION,
            language=state.language,
            explanation_key="dispute.none",
        )
    row = rows[0]
    _emit(ports, state.language.value, step="decide", policy_rule="dispute.status")
    return TurnOutput(
        kind=OutcomeKind.EXPLANATION,
        language=state.language,
        explanation_key="dispute.status",
        explanation_values={"case_id": row.case_id, "case_status": row.status},
    )


def _correction_target(turn: TextInput, state: ConversationState, ports: Ports) -> Candidate | None:
    """A charge that the message grounds, different from the open box.

    With the box open, a correction ("no, el de 320") must close it and ground
    the new charge. The parsers run here; the normal loop then shows the new box.
    """
    pending = state.pending_confirmation
    if pending is None:
        return None
    try:
        candidates = ports.tools.lookup_transactions()
    except GoldTimeout:
        return None
    today = _today(ports)
    narrowed = narrow(turn.text, None, candidates, today)
    if narrowed.match is not None and narrowed.match.candidate_id != pending.candidate_id:
        return narrowed.match
    if narrowed.stated and len(narrowed.candidates) == 1:
        only = narrowed.candidates[0]
        if only.candidate_id != pending.candidate_id:
            return only
    return None


def _charge_status(
    turn: TextInput, state: ConversationState, ports: Ports, understood: UnderstandResult
) -> TurnOutput:
    """Answer the status of the verified charge. Never opens a box (REQ-0003)."""
    looked = _lookup_transactions(state, ports)
    if isinstance(looked, TurnOutput):
        return looked
    today = _today(ports)
    narrowed = narrow(turn.text, understood, looked, today)
    candidate = narrowed.match
    if candidate is None and narrowed.candidates:
        # No charge named: the newest verified charge is "the last charge".
        candidate = narrowed.candidates[0]
    if candidate is None:
        return TurnOutput(
            kind=OutcomeKind.QUESTION,
            language=state.language,
            reason="charge.not_found",
            text=_draft_text(understood, DraftFacts(), state, ports),
        )
    policy = load_country(ports.country)
    eligible = bool(
        policy
        and policy.disputable.get(candidate.status.value, False)
        and not _expired(candidate, today, policy.window_days)
        and not candidate.is_disputed
    )
    state.candidates = [candidate]
    _emit(ports, state.language.value, step="decide", policy_rule="charge.status")
    facts = DraftFacts(
        merchant=candidate.merchant,
        amount=candidate.amount,
        date=candidate.date,
        status=candidate.status.value,
    )
    base = "charge.status" if eligible else "charge.statusIneligible"
    return TurnOutput(
        kind=OutcomeKind.EXPLANATION,
        language=state.language,
        reason="charge.status",
        explanation_key=_variant_key(base, max(len(state.turns) - 1, 0)),
        explanation_values={
            "merchant": candidate.merchant,
            "amount": candidate.amount,
            "status": candidate.status.value,
            "charge_date": candidate.date,
            "eligible": eligible,
        },
        text=_draft_text(understood, facts, state, ports),
    )


def _on_text(turn: TextInput, state: ConversationState, ports: Ports) -> TurnOutput:
    state.turns.append(turn.text)
    if len(state.turns) > MAX_TURNS:
        del state.turns[: len(state.turns) - MAX_TURNS]
    today = ports.today or date.today()
    merchants = [item.merchant for item in state.candidates]
    if is_why_followup(turn.text, merchants, today.year):
        # Answer from the stored decision only: no model, no lookup, no engine.
        return _explanation(state, ports)
    if refuse_extraction(turn.text, merchants):
        state.language = _message_language(turn.text, state.language)
        return _extraction_refusal(state, ports)
    if _is_dispute_status_question(turn.text):
        state.language = _message_language(turn.text, state.language)
        return _dispute_status(state, ports)
    if is_injection(turn.text):
        state.language = _message_language(turn.text, state.language)
        _emit(ports, state.language.value, step="decide", policy_rule="injection_suspected")
    if state.pending_confirmation is not None:
        # The box swallows everything except a person request or a correction
        # that grounds another charge. The model is not consulted here for
        # anything else, so a failure cannot change this.
        if _model_says_person(turn.text, state, ports) is True:
            return _person_request(state, ports)
        if _correction_target(turn, state, ports) is None:
            return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language, text=turn.text)
        # A correction: close the box and let the normal loop ground the new charge.
        state.pending_confirmation = None
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
    # A why question that names a charge is grounded below, not clarified here.
    if understood.kind is UnderstandKind.MISSING and not asks_why(turn.text):
        subtype = _opener_subtype(turn.text, understood)
        if subtype is not None:
            base = f"opener.{subtype}"
            return TurnOutput(
                kind=OutcomeKind.EXPLAIN,
                language=state.language,
                reason=base,
                message_key=_variant_key(base, max(len(state.turns) - 1, 0)),
                text=_draft_text(understood, DraftFacts(), state, ports),
            )
        capped = _capped(state, ports)
        if capped is not None:
            return capped
        state.clarification_count += 1
        _record_question(state, "missing")
        return TurnOutput(
            kind=OutcomeKind.QUESTION,
            language=state.language,
            text=_draft_text(understood, DraftFacts(), state, ports),
        )
    # A why question about a named charge is answered from the rule below, even
    # when the model labels it as a status question.
    if understood.kind is UnderstandKind.STATUS and not asks_why(turn.text):
        return _charge_status(turn, state, ports, understood)
    if understood.kind is UnderstandKind.OUT_OF_SCOPE:
        # Decision 008: say what is out of scope and offer the advisor; a model
        # error costs a sentence, not a ticket. The customer can ask for the
        # advisor at any time; without that, a third out-of-scope turn in a
        # row hands off.
        state.scope_asks += 1
        if state.scope_asks <= MAX_SCOPE_OFFERS:
            subtype = (
                understood.subtype if understood.subtype in SUBTYPE_OUT_OF_SCOPE else None
            )
            base = f"out_of_scope.{subtype}" if subtype else "out_of_scope.ask"
            _emit(ports, state.language.value, step="decide", policy_rule=base)
            return TurnOutput(
                kind=OutcomeKind.OFFER,
                language=state.language,
                reason=base,
                message_key=_variant_key(base, max(len(state.turns) - 1, 0)),
                text=_draft_text(understood, DraftFacts(), state, ports),
            )
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
    looked = _lookup_transactions(state, ports)
    if isinstance(looked, TurnOutput):
        return looked
    candidates = looked
    today = _today(ports)
    narrowed = narrow(turn.text, understood, candidates, today)
    if narrowed.match is None:
        capped = _capped(state, ports)
        if capped is not None:
            return capped
        state.clarification_count += 1
        _record_question(state, "which_charge")
        if understood.not_mine:
            # The customer denied what was shown: never show it again.
            _remember_rejected(state, [item.candidate_id for item in state.candidates])
        state.candidates = [
            item for item in narrowed.candidates if item.candidate_id not in state.rejected_ids
        ][:4]
        return TurnOutput(
            kind=OutcomeKind.QUESTION,
            language=state.language,
            reason="charge.not_found" if narrowed.not_found else None,
            explanation_values=(
                {"searched_date": narrowed.searched_date} if narrowed.searched_date else {}
            ),
            text=_draft_text(understood, DraftFacts(), state, ports),
        )
    if asks_why(turn.text):
        # Why about a named charge: ground it and decide. An explainable rule
        # answers from the rule; a safety rule stays a new request, so naming
        # the charge never skips verification (adversarial F6).
        hit = _hit(state, ports, Intent.CHARGE, narrowed.match)
        if hit.outcome is HitOutcome.EXPLAIN:
            return _explanation(state, ports)
    # Repair: new facts re-anchor to this charge; any previously shown charge
    # that is not the match is superseded and joins the rejected list.
    _remember_rejected(
        state,
        [item.candidate_id for item in state.candidates],
        keep=narrowed.match.candidate_id,
    )
    _forget_rejected(state, narrowed.match.candidate_id)
    state.candidates = candidates
    return _after_policy(state, ports, Intent.CHARGE, narrowed.match, turn.text)


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
    if time() - pending.created_at > CONFIRM_TTL_S:
        # Late confirmation: never write, show the candidate again with a
        # fresh box instead of the stale one.
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
    if hit.rule_id in EXPLAINABLE_RULES:
        # Remember only decisions that have an explanation; confirmations and
        # case creation must not overwrite the decision the customer saw.
        state.last_decision = LastDecision(
            rule_id=hit.rule_id,
            candidate_id=None if candidate is None else candidate.candidate_id,
            policy_version=None if policy is None else policy.version,
            values=decision_snapshot(hit.rule_id, candidate, today, policy),
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
