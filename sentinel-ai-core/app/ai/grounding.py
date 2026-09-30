import re
import unicodedata
from dataclasses import dataclass
from datetime import date
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
