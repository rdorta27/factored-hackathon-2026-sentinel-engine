"""Deterministic "why" recognition and explanation mapping (REQ-0033).

A why follow-up is answered from the stored decision, never recomputed: the
model, the lookup tool and the policy engine are not called. Recognition is a
small per-language pattern set (es-419, pt-BR) and is rejected as soon as the
message names a charge, which is then a new request. The answer carries a
translation key and verified values only; no prose is authored here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.ai.grounding import extract_facts, normalize_text
from app.orchestrator.types import LastDecision
from app.policy.engine import RULE_EXPLANATIONS, WITHHELD_EXPLANATIONS

# Reason questions, accent-insensitive. Deliberately narrow: "porque" (because)
# and a bare "explícame" are not why questions, and would hijack a new request.
_WHY_PATTERNS = (
    r"\bpor que\b",
    r"\ben que te basas\b",
    r"\ben que se basa\b",
    r"\bde donde sale\b",
    r"\bde donde salen\b",
    r"\bde donde viene\b",
    r"\bde donde vienen\b",
    r"\ba que se debe\b",
    r"\bpor que motivo\b",
    r"\bpor que razon\b",
    r"\bcon que criterio\b",
    r"\bcomo lo sabes\b",
    r"\bcomo sabes\b",
    r"\bcom base em que\b",
    r"\bem que se baseia\b",
    r"\bde onde vem\b",
    r"\bde onde saem\b",
    r"\bde onde surgiu\b",
    r"\bpor qual motivo\b",
    r"\bpor qual razao\b",
    r"\bcom que criterio\b",
    r"\bcomo voce sabe\b",
)
_WHY = tuple(re.compile(pattern) for pattern in _WHY_PATTERNS)
# A number followed by a time unit is the window being quoted, not a charge.
_WINDOW_PHRASE = re.compile(r"\b\d+\s*(?:dias?|days?)\b")

NONE_KEY = "explanation.none"
SAFETY_KEY = "explanation.safety"
# The safety reply must not say which rule fired (decision 010/011), so the
# three safety rules share one neutral id instead of exposing fraud.score.
SAFETY_RULE = "advisor.review"


@dataclass(frozen=True)
class Explanation:
    """The mapped answer: one of the three kinds, never model prose."""

    kind: str
    message_key: str
    rule_id: str | None = None
    values: dict[str, Any] = field(default_factory=dict)


def asks_why(message: str) -> bool:
    """True when the message asks the reason for a decision."""
    text = normalize_text(message)
    return any(pattern.search(text) for pattern in _WHY)


def names_a_charge(message: str, merchants: list[str], reference_year: int) -> bool:
    """True when the message states a merchant, a date or an amount.

    The window quoted in a why question ("los 90 días") is not a charge, so it
    is removed before reading an amount.
    """
    facts = extract_facts(message, reference_year, merchants)
    if facts.merchant or facts.date_iso or facts.month:
        return True
    without_window = _WINDOW_PHRASE.sub(" ", normalize_text(message))
    return extract_facts(without_window, reference_year, []).amount is not None


def is_why_followup(message: str, merchants: list[str], reference_year: int) -> bool:
    """A reason question that names no charge is a follow-up on the last decision."""
    return asks_why(message) and not names_a_charge(message, merchants, reference_year)


def explanation_for(last: LastDecision | None) -> Explanation:
    """Map the stored decision to one of the three explanation kinds."""
    if last is None:
        # No decision: say what the service can do, invent no rule.
        return Explanation("none", NONE_KEY)
    if last.rule_id in WITHHELD_EXPLANATIONS:
        # One fixed sentence for all three safety rules (decisions 010, 011).
        return Explanation("withheld", SAFETY_KEY, SAFETY_RULE)
    if last.rule_id in RULE_EXPLANATIONS:
        return Explanation("rule", f"explanation.{last.rule_id}", last.rule_id, dict(last.values))
    return Explanation("none", NONE_KEY)
