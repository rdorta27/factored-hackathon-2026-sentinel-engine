"""Validator for model-written reply drafts (decision 024).

The model writes the words of turns that do not decide, with placeholders
only for values: ``{merchant}``, ``{amount}``, ``{date}``, ``{status}``. Code
fills each placeholder from the verified facts of the turn. This module
refuses any draft that carries a value of its own, and records the reason so
the turn log can mark it ``draft_rejected``. A rejected draft falls back to
the template of the turn. Turns that decide never use a draft.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

ALLOWED_PLACEHOLDERS = frozenset({"merchant", "amount", "date", "status"})
MAX_DRAFT_CHARS = 280

_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_DIGIT_RE = re.compile(r"\d")
_QUOTED_RE = re.compile(r'"([^"]+)"|“([^”]+)”|«([^»]+)»')
_WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÂÊÔÃÕÇÑáéíóúüâêôãõçñ]+")
_SENTENCE_SPLIT_RE = re.compile(r"[.?!…]+\s*")

# A time, refund or result promise the model must never make. Checked on the
# lowered text after the greeting phrases below are removed, so "buenos días"
# does not trip the "días" mark. Biased to safety: a false hit falls back to
# the template, which is always acceptable.
_GREETING_PHRASES = ("buenos días", "buenos dias", "bom dia", "boa tarde", "buenas tardes", "boa noite")
_PROMISE_MARKS = (
    "reembols",
    "devolv",
    "estorn",
    "refund",
    "garant",
    "promet",
    "asegur",
    "assegur",
    "compens",
    "acredit",
    "resolveremos",
    "resolverei",
    "aprobado",
    "aprovado",
    "resuelto",
    "resolvido",
    "caso cerrado",
    "caso encerrado",
    "24 horas",
    "48 horas",
    "días hábiles",
    "dias úteis",
    "días utiles",
)
# Whole-word time promises: "en unos días" is a promise, "buenos días" is not.
_TIME_WORDS = ("días", "dias", "semana", "semanas", "mañana", "amanhã", "horas")

# Marks that belong to one reply language only. The check is one-sided: a
# draft is refused only when it shows marks of the other language. A short
# draft with no marks in either list passes the language check.
_PT_ONLY_MARKS = (
    "não",
    "você",
    "voce",
    "obrigad",
    "estou",
    "bom dia",
    "tudo bem",
    "gentileza",
    "cobrança",
    "cobranca",
    "à disposição",
    "a disposicao",
)
_ES_ONLY_MARKS = (
    "gracias",
    "hola",
    "usted",
    "puedo",
    "quiero",
    "con gusto",
    "cuénteme",
    "cuenteme",
    "ayudarle",
)

# Common capitalized words that are not names, so fluent text is not refused.
_NAME_STOPLIST = frozenset(
    {
        "español",
        "espanol",
        "português",
        "portugues",
        "banco",
        "banca",
        "sentinel",
    }
)


@dataclass(frozen=True)
class DraftFacts:
    """The verified facts of the turn. None means the turn has no value."""

    merchant: str | None = None
    amount: str | None = None
    date: str | None = None
    status: str | None = None


def _fact_values(facts: DraftFacts) -> tuple[str, ...]:
    return tuple(value for value in (facts.merchant, facts.amount, facts.date, facts.status) if value)


def _strip_placeholders(draft: str) -> str:
    return _PLACEHOLDER_RE.sub(" ", draft)


def _check_placeholders(draft: str) -> str | None:
    for match in _PLACEHOLDER_RE.finditer(draft):
        if match.group(1) not in ALLOWED_PLACEHOLDERS:
            return "unknown_placeholder"
    return None


def _check_names(text: str, facts: DraftFacts) -> str | None:
    known = [value.lower() for value in _fact_values(facts)]
    for match in _QUOTED_RE.finditer(text):
        span = next(part for part in match.groups() if part)
        if span.strip().lower() not in known:
            return "unverified_name"
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        tokens = _WORD_RE.findall(sentence)
        for token in tokens[1:]:
            if len(token) < 3 or not token[0].isupper():
                continue
            lowered = token.lower()
            if lowered in _NAME_STOPLIST or lowered in known:
                continue
            if any(lowered in value for value in known):
                continue
            return "unverified_name"
    return None


def _check_promise(text: str) -> str | None:
    lowered = text.lower()
    for phrase in _GREETING_PHRASES:
        lowered = lowered.replace(phrase, " ")
    if any(mark in lowered for mark in _PROMISE_MARKS):
        return "promise"
    words = set(_WORD_RE.findall(lowered))
    if words & set(_TIME_WORDS):
        return "promise"
    return None


def _check_language(text: str, language: str) -> str | None:
    lowered = text.lower()
    if language == "pt-BR":
        if any(mark in lowered for mark in _ES_ONLY_MARKS):
            return "wrong_language"
        return None
    if any(mark in lowered for mark in _PT_ONLY_MARKS):
        return "wrong_language"
    return None


def validate_draft(draft: str | None, facts: DraftFacts, language: str) -> tuple[bool, str]:
    """Check a model-written draft. Return (True, "ok") or (False, reason).

    Reasons: "empty", "unknown_placeholder", "digit_outside_placeholder",
    "raw_value_outside_placeholder", "unverified_name", "promise",
    "wrong_language", "too_long". The checks run in that order.
    """
    if not isinstance(draft, str) or not draft.strip():
        return False, "empty"
    if len(draft) > MAX_DRAFT_CHARS:
        return False, "too_long"
    reason = _check_placeholders(draft)
    if reason is not None:
        return False, reason
    text = _strip_placeholders(draft)
    if _DIGIT_RE.search(text):
        return False, "digit_outside_placeholder"
    for value in _fact_values(facts):
        if value.strip() and value.strip().lower() in text.lower():
            return False, "raw_value_outside_placeholder"
    reason = _check_names(text, facts)
    if reason is not None:
        return False, reason
    reason = _check_promise(text)
    if reason is not None:
        return False, reason
    reason = _check_language(text, language)
    if reason is not None:
        return False, reason
    return True, "ok"


def fill_draft(draft: str, facts: DraftFacts) -> str:
    """Fill the placeholders of a validated draft with the verified facts.

    Only call with a draft that passed ``validate_draft``. A placeholder with
    no verified value renders as an empty string.
    """
    values = {"merchant": facts.merchant, "amount": facts.amount, "date": facts.date, "status": facts.status}

    def _sub(match: re.Match[str]) -> str:
        value = values.get(match.group(1))
        return value if value else ""

    return _PLACEHOLDER_RE.sub(_sub, draft)
