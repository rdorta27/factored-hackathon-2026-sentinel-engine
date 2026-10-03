"""Deterministic checks that run on masked text before the model.

Extraction refuses a request to reveal the prompt. Injection is only recorded.
A message that also names a charge is not an extraction refusal: the charge
path still runs, and the reply carries keys only.
"""

import re

from app.ai.grounding import extract_facts, normalize_text

_VERB = (
    r"(?:repite|repita|repetir|copia|copie|copiar|copiame|"
    r"revela|revele|revelar|muestrame|mostra|mostre)"
)
_NOUN = r"(?:prompt|instrucciones|instrucoes|configuracion|configuracao)"
_EXTRACT = re.compile(rf"(?:{_VERB}.{{0,48}}{_NOUN}|{_NOUN}.{{0,48}}{_VERB})")
_INJECT = (
    re.compile(
        r"\b(?:ignora|ignore|olvidate|olvida|esqueca)\b.{0,40}"
        r"\b(?:instrucciones|instrucoes|reglas|regras|politica)\b"
    ),
    re.compile(r"\b(?:ignora|ignore)\b.{0,24}\bpaso de confirmacion\b"),
    re.compile(r"\b(?:salta|salte)\b.{0,30}\b(?:confirmacion|validacion)\b"),
    re.compile(r"\bsin\s+(?:pedirme\s+)?confirm"),
    re.compile(r"\bsem\s+pedir\s+confirm"),
    re.compile(r"\bsin\s+confirmar\b"),
    re.compile(r"\bmodo\s+(?:administrador|admin|debug|sistema)\b"),
    re.compile(r"\b(?:eres|sos|actua como|aja como)\b.{0,24}\badministrador\b"),
    re.compile(r"\[admin\]"),
    re.compile(r"\bsistema\s*:"),
    re.compile(r"</?\s*(?:instrucciones|instrucoes|system|sistema|admin)\s*>"),
)
_REFERENCE = re.compile(r"\bTXN-\d+\b", re.IGNORECASE)


def is_extraction(text: str) -> bool:
    """A request to reveal, repeat or copy the prompt, instructions or configuration."""
    return _EXTRACT.search(normalize_text(text)) is not None


def is_injection(text: str) -> bool:
    """Ignore-instructions, skip-confirmation, admin or system mode, or a fake tag."""
    normalized = normalize_text(text)
    return any(pattern.search(normalized) for pattern in _INJECT)


def names_charge(text: str, merchants: list[str] | None = None) -> bool:
    """True when the existing parsers see an amount, a merchant or a reference."""
    facts = extract_facts(text, 2026, list(merchants or []))
    if facts.amount or facts.merchant:
        return True
    return _REFERENCE.search(text) is not None


def refuse_extraction(text: str, merchants: list[str] | None = None) -> bool:
    return is_extraction(text) and not names_charge(text, merchants)
