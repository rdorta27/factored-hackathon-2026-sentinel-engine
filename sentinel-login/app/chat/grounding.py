"""Statement parsing and transaction grounding.

The customer's words are the source of truth: a case may only be opened for a
transaction those words actually describe. Parsing is bilingual (Spanish and
Portuguese) and separator-agnostic, because both ``1.000,00`` and ``1,000.00``
appear in LATAM messages.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.gold.store import GoldRow

# Month names in Spanish and Portuguese, both with and without accents.
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

DISPUTE_WORDS = (
    "dispute", "disputa", "charge", "cargo", "cobro", "cobranca", "cobrança",
    "reclamo", "reclamacao", "reclamação", "desconozco", "nao reconheco",
    "não reconheço", "$", "r$",
)

_AMOUNT_RE = re.compile(
    r"(?:r\$\s*)?(\d{1,3}(?:[.,\s]\d{3})+(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?(?![\d.,]))"
)
_DAY_RE = re.compile(r"\b(\d{1,2})\s*(?:de\s+)?([a-zç]+)\b")
_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def normalize_text(value: str) -> str:
    """Lowercase, strip accents, collapse whitespace for comparison."""
    decomposed = unicodedata.normalize("NFKD", value.lower())
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", without_accents).strip()


def normalize_amount(value: str) -> str | None:
    """Return a canonical '1234.56' string, or None when unparseable.

    The separator that appears last is the decimal one, so ``1.000,00`` and
    ``1,000.00`` both mean one thousand.
    """
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
        # "1.000" means one thousand; "1000.00" means one thousand exactly.
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
    """Find a date in the message and return it as ISO, or None."""
    iso = _ISO_RE.search(text)
    if iso:
        return f"{iso.group(1)}-{iso.group(2)}-{iso.group(3)}"
    # "20 de septiembre" / "20 setembro" (day first month second)
    for match in _DAY_RE.finditer(text):
        day, month_name = int(match.group(1)), match.group(2)
        month = MONTHS.get(month_name)
        if month and 1 <= day <= 31:
            return date(reference_year, month, day).isoformat()
    return None


def parse_amount(text: str) -> str | None:
    """Find the amount the customer wrote and normalize it.

    A single separator is ambiguous by nature: ``1000.00`` has two decimals
    while ``1.000`` has three digits after the dot. The digit count right
    after the separator decides, which keeps both ``1.000,00`` and ``1000.00``
    working without guessing.
    """
    for match in _AMOUNT_RE.finditer(text):
        normalized = normalize_amount(match.group(1))
        if normalized and normalized != "0.00":
            return normalized
    return None


def _looks_like_amount(token: str) -> bool:
    if not any(ch.isdigit() for ch in token):
        return False
    last_sep = max(token.rfind(","), token.rfind("."))
    if last_sep == -1:
        return True
    decimals = re.sub(r"\D", "", token[last_sep + 1:])
    return not (last_sep > 0 and len(decimals) == 3 and "," not in token[:last_sep] and "." not in token[:last_sep])


def parse_merchant(text: str, known: list[str]) -> str | None:
    """Return the known merchant the message names, if any."""
    normalized = normalize_text(text)
    for merchant in known:
        if merchant and normalize_text(merchant) in normalized:
            return merchant
    return None


@dataclass(frozen=True)
class StatedFacts:
    """What the customer actually said. Missing fields stay None."""

    date_iso: str | None
    amount: str | None
    merchant: str | None

    def describes_anything(self) -> bool:
        return any([self.date_iso, self.amount, self.merchant])


@dataclass(frozen=True)
class Grounding:
    """Outcome of comparing the statement against the customer's rows."""

    outcome: Literal["matched", "ambiguous", "none"]
    candidates: list[GoldRow]
    match: GoldRow | None


def extract_facts(message: str, reference_year: int, merchants: list[str]) -> StatedFacts:
    text = normalize_text(message)
    return StatedFacts(
        date_iso=parse_date(text, reference_year),
        amount=parse_amount(text),
        merchant=parse_merchant(message, merchants),
    )


def ground(
    facts: StatedFacts, rows: list[GoldRow], reference_year: int
) -> Grounding:
    """Match stated facts against the customer's transactions.

    Only facts the customer actually stated are compared, so a message that
    names just the merchant still matches every charge at that merchant (which
    is ambiguity, not a match). Facts that contradict a row exclude it.
    """
    stated = [f for f in (facts.date_iso, facts.amount, facts.merchant) if f]
    if not stated:
        return Grounding("none", list(rows), None)

    matches: list[GoldRow] = []
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


def rank_candidates(
    facts: StatedFacts | None, rows: list[GoldRow], today: date | None = None
) -> list[GoldRow]:
    """Order candidates by similarity to what the customer said.

    Merchant, then amount, then date proximity to the reference date. Rows
    outside the window are pushed last, because they cannot be disputed.
    """
    reference = today or date.today()

    def score(row: GoldRow) -> tuple:
        merchant_hit = (
            1
            if facts is not None
            and facts.merchant
            and normalize_text(row.merchant) == normalize_text(facts.merchant)
            else 0
        )
        amount_hit = (
            1
            if facts is not None
            and facts.amount
            and normalize_amount(row.amount) == facts.amount
            else 0
        )
        try:
            age = abs((reference - date.fromisoformat(row.date)).days)
        except ValueError:
            age = 10_000
        return (-merchant_hit, -amount_hit, age)

    return sorted(rows, key=score)
