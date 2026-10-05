"""Frozen copy of `app/ai/grounding.py` before the change chat-start (commit 279d6a5).

It is the configuration `rules_fixed` of the charge-selector evaluation. Do not edit it.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from app.orchestrator.types import Candidate

MONTHS = {
    "enero": 1, "ene": 1, "janeiro": 1, "jan": 1,
    "febrero": 2, "feb": 2, "fevereiro": 2, "fev": 2,
    "marzo": 3, "mar": 3, "marco": 3, "março": 3,
    "abril": 4, "abr": 4,
    "mayo": 5, "may": 5, "maio": 5, "mai": 5,
    "junio": 6, "jun": 6, "junho": 6,
    "julio": 7, "jul": 7, "julho": 7,
    "agosto": 8, "ago": 8,
    "septiembre": 9, "setiembre": 9, "sep": 9, "set": 9, "setembro": 9,
    "octubre": 10, "oct": 10, "outubro": 10, "out": 10,
    "noviembre": 11, "nov": 11, "novembro": 11,
    "diciembre": 12, "dic": 12, "dezembro": 12, "dez": 12,
}

_AMOUNT_RE = re.compile(
    r"(?:r\$\s*)?(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?(?![\d.,]))"
)
_DAY_RE = re.compile(r"\b(\d{1,2})\s*(?:de\s+)?([a-zç]+)\b")
_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
# Design: drop these before a token is compared with a merchant. Short words
# that are not in the list simply fail the four-letter prefix rule.
STOP_WORDS = frozenset({"la", "el", "de", "do", "da", "na"})
PREFIX_MIN = 4
_RELATIVE_DAYS = {
    "hoy": 0, "hoje": 0,
    "ayer": 1, "ontem": 1,
    "anteayer": 2, "anteontem": 2,
}
_WEEKDAYS = {
    "lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6,
    "segunda": 0, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4,
}
_DATE_WORDS = frozenset(_RELATIVE_DAYS) | frozenset(_WEEKDAYS) | frozenset(MONTHS) | frozenset({
    "semana", "pasada", "passada", "hace", "ha", "faz", "dias", "dia", "feira",
})
# Words that introduce a charge, not a merchant, so "en el cargo" is not a name.
_NOT_MERCHANT = frozenset({
    "cargo", "cargos", "cobro", "cobros", "cobranca", "cobrancas", "compra", "compras",
    "movimiento", "movimientos", "vez", "veces", "mismo", "misma", "reconozco", "reconoce",
    "hice", "hizo", "quiero", "revisar", "cuenta", "tarjeta", "cartao", "que", "por",
    "con", "para", "una", "uno", "este", "esta", "ese", "esa", "meu", "minha",
})
_REPEATED_RE = re.compile(r"\b(?:dos veces|duas vezes|doble|duplicad\w*|em dobro)\b")
_HACE_RE = re.compile(r"\b(?:hace|ha|faz)\s+(\d+)\s+dias?\b")
_WEEK_RE = re.compile(r"\b(?:la\s+)?semana\s+(?:pasada|passada)\b")
_PHRASE_RE = re.compile(r"\b(?:en|de|del|na|do|da|em)\s+((?:[a-z]{2,}\s+){0,3}[a-z]{3,})")


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.lower())
    without = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without).strip()


def normalize_amount(value: str) -> str | None:
    cleaned = value.replace("r$", "").replace("$", "").strip()
    cleaned = re.sub(r"\s", "", cleaned)
    if not cleaned or not any(ch.isdigit() for ch in cleaned):
        return None
    last_comma = cleaned.rfind(",")
    last_dot = cleaned.rfind(".")
    if last_comma > last_dot:
        integer = cleaned[:last_comma].replace(".", "").replace(",", "")
        decimals = cleaned[last_comma + 1:]
    elif last_dot > last_comma:
        after = cleaned[last_dot + 1:]
        if len(after) == 3 and "," not in cleaned[:last_dot] and "." not in cleaned[:last_dot]:
            integer, decimals = cleaned.replace(".", ""), ""
        else:
            integer = cleaned[:last_dot].replace(",", "")
            decimals = after
    else:
        integer, decimals = cleaned, ""
    if not integer.isdigit() or (decimals and not decimals.isdigit()):
        return None
    decimals = (decimals + "00")[:2] if decimals else "00"
    return f"{int(integer)}.{decimals}"


def parse_date(text: str, reference_year: int) -> str | None:
    iso = _ISO_RE.search(text)
    if iso:
        return f"{iso.group(1)}-{iso.group(2)}-{iso.group(3)}"
    for match in _DAY_RE.finditer(text):
        day, month_name = int(match.group(1)), match.group(2)
        month = MONTHS.get(month_name)
        if month and 1 <= day <= 31:
            return date(reference_year, month, day).isoformat()
    return None


def parse_amount(text: str) -> str | None:
    found: list[str] = []
    for match in _AMOUNT_RE.finditer(text):
        normalized = normalize_amount(match.group(1))
        if normalized and normalized != "0.00":
            found.append(normalized)
    if not found:
        return None
    grouped = [
        normalize_amount(match.group(1))
        for match in _AMOUNT_RE.finditer(text)
        if re.search(r"[.,]", match.group(1))
    ]
    grouped = [value for value in grouped if value and value != "0.00"]
    return grouped[0] if grouped else found[0]


def parse_merchant(text: str, known: list[str]) -> str | None:
    normalized = normalize_text(text)
    for merchant in known:
        if merchant and normalize_text(merchant) in normalized:
            return merchant
    return None


@dataclass(frozen=True)
class StatedFacts:
    date_iso: str | None
    amount: str | None
    merchant: str | None


@dataclass(frozen=True)
class Grounding:
    outcome: Literal["matched", "ambiguous", "none"]
    candidates: list[Candidate]
    match: Candidate | None


def extract_facts(message: str, reference_year: int, merchants: list[str]) -> StatedFacts:
    text = normalize_text(message)
    return StatedFacts(
        date_iso=parse_date(text, reference_year),
        amount=parse_amount(text),
        merchant=parse_merchant(message, merchants),
    )


def ground(facts: StatedFacts, rows: list[Candidate]) -> Grounding:
    stated = [value for value in (facts.date_iso, facts.amount, facts.merchant) if value]
    if not stated:
        return Grounding("none", list(rows), None)
    matches: list[Candidate] = []
    for row in rows:
        if facts.date_iso and row.date != facts.date_iso:
            continue
        if facts.amount and normalize_amount(row.amount) != facts.amount:
            continue
        if facts.merchant and normalize_text(row.merchant) != normalize_text(facts.merchant):
            continue
        matches.append(row)
    if len(matches) == 1:
        return Grounding("matched", matches, matches[0])
    if matches:
        return Grounding("ambiguous", matches, None)
    return Grounding("none", list(rows), None)


def rank_candidates(facts: StatedFacts | None, rows: list[Candidate], today: date) -> list[Candidate]:
    def score(row: Candidate) -> tuple:
        merchant_hit = (
            1
            if facts is not None
            and facts.merchant
            and normalize_text(row.merchant) == normalize_text(facts.merchant)
            else 0
        )
        amount_hit = (
            1
            if facts is not None and facts.amount and normalize_amount(row.amount) == facts.amount
            else 0
        )
        try:
            age = abs((today - date.fromisoformat(row.date)).days)
        except ValueError:
            age = 10_000
        return (-merchant_hit, -amount_hit, age)

    return sorted(rows, key=score)


def _content_tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", normalize_text(text))
        if token not in STOP_WORDS and not token.isdigit()
    ]


def shares_prefix(left: str, right: str, minimum: int = PREFIX_MIN) -> bool:
    """True when the two tokens share a prefix of at least `minimum` letters."""
    shared = 0
    for a, b in zip(left, right):
        if a != b:
            break
        shared += 1
    return shared >= minimum


def token_matches_merchant(token: str, merchant: str) -> bool:
    for part in _content_tokens(merchant):
        if token == part or shares_prefix(token, part):
            return True
    return False


def _phrase_tokens(text: str) -> list[str]:
    """Tokens a preposition introduces as a possible merchant name."""
    found: list[str] = []
    for match in _PHRASE_RE.finditer(normalize_text(text)):
        for token in _content_tokens(match.group(1)):
            if token in _DATE_WORDS or token in _NOT_MERCHANT or len(token) < 3:
                continue
            found.append(token)
    return found


def stated_merchant_tokens(text: str, merchants: list[str]) -> tuple[str, ...]:
    """Merchant words the customer stated.

    A token counts when it soft-matches a known merchant, or when a preposition
    introduces it as a name. Every stated token must then fit the same row, so
    "Tienda Lumbre" does not collapse onto "Tienda del Sur".
    """
    tokens = []
    for token in _content_tokens(text):
        if token in _DATE_WORDS or token in _NOT_MERCHANT or len(token) < 3:
            continue
        if any(token_matches_merchant(token, merchant) for merchant in merchants):
            tokens.append(token)
    for token in _phrase_tokens(text):
        if token not in tokens:
            tokens.append(token)
    return tuple(tokens)


def relative_dates(text: str, reference: date) -> frozenset[str]:
    """Dates a relative phrase names, read from the reference date.

    Weekday names resolve to the most recent such day on or before the
    reference date. "semana pasada" / "semana passada" is the seven days
    before the reference date, not including it.
    """
    normalized = normalize_text(text)
    if _WEEK_RE.search(normalized):
        return frozenset((reference - timedelta(days=n)).isoformat() for n in range(1, 8))
    hace = _HACE_RE.search(normalized)
    if hace:
        return frozenset({(reference - timedelta(days=int(hace.group(1)))).isoformat()})
    for word, offset in sorted(_RELATIVE_DAYS.items(), key=lambda item: -len(item[0])):
        if re.search(rf"\b{word}\b", normalized):
            return frozenset({(reference - timedelta(days=offset)).isoformat()})
    for name, weekday in _WEEKDAYS.items():
        if re.search(rf"\b{name}\b", normalized):
            delta = (reference.weekday() - weekday) % 7
            return frozenset({(reference - timedelta(days=delta)).isoformat()})
    return frozenset()


def is_repeated_charge(text: str) -> bool:
    return _REPEATED_RE.search(normalize_text(text)) is not None


@dataclass(frozen=True)
class SoftFacts:
    merchant_tokens: tuple[str, ...]
    dates: frozenset[str]
    repeated: bool


def extract_soft(message: str, reference: date, merchants: list[str]) -> SoftFacts:
    return SoftFacts(
        merchant_tokens=stated_merchant_tokens(message, merchants),
        dates=relative_dates(message, reference),
        repeated=is_repeated_charge(message),
    )


def _newest(rows: list[Candidate]) -> list[Candidate]:
    return sorted(rows, key=lambda row: row.date, reverse=True)


def _pair_key(row: Candidate) -> tuple[str, str]:
    return (normalize_text(row.merchant), normalize_amount(row.amount) or row.amount)


@dataclass(frozen=True)
class Narrowing:
    candidates: list[Candidate]
    not_found: bool
    stated: bool


def narrow_candidates(
    facts: StatedFacts,
    soft: SoftFacts,
    rows: list[Candidate],
    today: date,
) -> Narrowing:
    """Filter by every stated detail. Soft facts never select a charge.

    A row is dropped only when a stated detail contradicts it. When details
    were stated and nothing is left, the newest rows come back with
    `not_found` so the reply can say so.
    """
    stated = bool(
        facts.date_iso or facts.amount or facts.merchant
        or soft.merchant_tokens or soft.dates or soft.repeated
    )
    if not stated:
        return Narrowing(list(rows), False, False)
    pool = list(rows)
    dates = {facts.date_iso} if facts.date_iso else set(soft.dates)
    if dates:
        pool = [row for row in pool if row.date in dates]
    if facts.amount:
        pool = [row for row in pool if normalize_amount(row.amount) == facts.amount]
    if facts.merchant:
        wanted = normalize_text(facts.merchant)
        pool = [row for row in pool if normalize_text(row.merchant) == wanted]
    elif soft.merchant_tokens:
        pool = [
            row for row in pool
            if all(token_matches_merchant(token, row.merchant) for token in soft.merchant_tokens)
        ]
    if soft.repeated:
        counts: dict[tuple[str, str], int] = {}
        for row in pool:
            key = _pair_key(row)
            counts[key] = counts.get(key, 0) + 1
        paired = {key for key, count in counts.items() if count >= 2}
        if not paired:
            return Narrowing(_newest(rows), True, True)
        pool = [row for row in pool if _pair_key(row) in paired]
    if not pool:
        return Narrowing(_newest(rows), True, True)

    def hits(row: Candidate) -> int:
        score = 0
        if facts.amount and normalize_amount(row.amount) == facts.amount:
            score += 1
        if facts.merchant and normalize_text(row.merchant) == normalize_text(facts.merchant):
            score += 1
        elif soft.merchant_tokens and all(
            token_matches_merchant(token, row.merchant) for token in soft.merchant_tokens
        ):
            score += 1
        if facts.date_iso and row.date == facts.date_iso:
            score += 1
        elif soft.dates and row.date in soft.dates:
            score += 1
        return score

    ordered = sorted(pool, key=lambda row: (-hits(row), _date_rank(row, today)))
    return Narrowing(ordered, False, True)


def _date_rank(row: Candidate, today: date) -> int:
    try:
        return abs((today - date.fromisoformat(row.date)).days)
    except ValueError:
        return 10_000
