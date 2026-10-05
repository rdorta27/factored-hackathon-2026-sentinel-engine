"""Examples for the charge selector, built from real transactions.

A description of one charge is team-generated text (simulation). The label is
the id of the transaction that the text was built from, so the label is exact.
The seed is fixed and the generator writes no rows: examples are rebuilt from
the local Gold file each time, and only counts and hashes go to git.

Splits (decision 025): by customer hash and by date of the target charge.
Two phrasing families appear only in the test split.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from app.ai.number_words import number_to_words
from app.orchestrator.types import Candidate, TransactionStatus

SEED = 20261004
VIEW = "v_service_dispute_eligible_transactions"
UNNAMED = "UNSPECIFIED"
MIN_CHARGES = 5
SPLITS = ("train", "validation", "test")
CUSTOMER_SHARE = {"train": (0, 60), "validation": (60, 80), "test": (80, 100)}
DATE_RANGE = {
    "train": ("0000-01-01", "2024-12-31"),
    "validation": ("2025-01-01", "2025-06-30"),
    "test": ("2025-07-01", "9999-12-31"),
}
TRAIN_FAMILIES = ("direct", "question", "terse")
TEST_ONLY_FAMILIES = ("story", "informal")
FAMILIES = TRAIN_FAMILIES + TEST_ONLY_FAMILIES
LOCALES = ("es-419", "pt-BR")

_MONTHS = {
    "es": "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(),
    "pt": "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split(),
}
_WEEKDAYS = {
    "es": "lunes martes miércoles jueves viernes sábado domingo".split(),
    "pt": "segunda terça quarta quinta sexta sábado domingo".split(),
}
_TYPES = {
    "es": {
        "Purchase": "una compra", "Transfer": "una transferencia", "Withdrawal": "un retiro",
        "Deposit": "un depósito", "Payment": "un pago", "Adjustment": "un ajuste",
    },
    "pt": {
        "Purchase": "uma compra", "Transfer": "uma transferência", "Withdrawal": "um saque",
        "Deposit": "um depósito", "Payment": "um pagamento", "Adjustment": "um ajuste",
    },
}
# Each family: opening words, then the order of the pieces, then closing words.
# The pt-BR line is the twin of the es-419 line, checked piece by piece in the
# tests. A piece the example leaves out is dropped.
_FAMILY = {
    "direct": {
        "es": ("No reconozco el cargo", ("type", "amount:de", "merchant:en", "date"), ""),
        "pt": ("Não reconheço a cobrança", ("type", "amount:de", "merchant:em", "date"), ""),
    },
    "question": {
        "es": ("¿Qué es el cobro", ("amount:de", "merchant:de", "date"), "?"),
        "pt": ("O que é a cobrança", ("amount:de", "merchant:de", "date"), "?"),
    },
    "terse": {
        "es": ("", ("merchant", "amount", "date", "type"), ""),
        "pt": ("", ("merchant", "amount", "date", "type"), ""),
    },
    "story": {
        "es": (
            "Revisando mi estado de cuenta vi un movimiento",
            ("date", "merchant:en", "amount:por"),
            "y no fui yo",
        ),
        "pt": (
            "Revisando meu extrato vi um lançamento",
            ("date", "merchant:em", "amount:por"),
            "e não fui eu",
        ),
    },
    "informal": {
        "es": ("oye me cobraron", ("amount", "merchant:en", "date"), "y yo no hice eso"),
        "pt": ("ei me cobraram", ("amount", "merchant:em", "date"), "e eu não fiz isso"),
    },
}


@dataclass(frozen=True)
class Row:
    transaction_id: str
    customer_id: str
    date: str
    amount: float
    currency: str
    merchant: str
    kind: str
    status: str


@dataclass(frozen=True)
class Example:
    example_id: str
    customer_id: str
    target_id: str
    today: str
    locale: str
    family: str
    split: str
    text: str
    has_merchant: bool
    amount_in_words: bool


def customer_bucket(customer_id: str) -> int:
    """0 to 99, from a hash of the customer id. The same id always gets the same bucket."""
    return int(hashlib.sha256(customer_id.encode()).hexdigest(), 16) % 100


def customer_split(customer_id: str) -> str:
    bucket = customer_bucket(customer_id)
    for split, (low, high) in CUSTOMER_SHARE.items():
        if low <= bucket < high:
            return split
    raise AssertionError(bucket)


def split_of_date(day: str) -> str | None:
    for split, (first, last) in DATE_RANGE.items():
        if first <= day <= last:
            return split
    return None


def to_candidate(row: Row, as_of: str) -> Candidate:
    return Candidate(
        candidate_id=row.transaction_id,
        status=TransactionStatus(row.status) if row.status in {s.value for s in TransactionStatus} else TransactionStatus.PENDING,
        amount=f"{row.amount:.2f}",
        currency=row.currency,
        merchant=row.merchant if row.merchant != UNNAMED else "",
        date=row.date,
        as_of=as_of,
    )


def gold_path() -> Path:
    """The local Gold file. Set SENTINEL_GOLD_DUCKDB when it is not in this checkout."""
    from app.services.gold_service import gold_duckdb_path

    found = gold_duckdb_path()
    if found is None:
        raise SystemExit("No local Gold file. Set SENTINEL_GOLD_DUCKDB to gold_bank.duckdb.")
    return found


def load_rows(db_path: Path, customer_ids: Iterable[str]) -> dict[str, list[Row]]:
    """Rows of the given customers, newest first. Reads the local Gold file read-only."""
    import duckdb

    ids = sorted(set(customer_ids))
    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        connection.execute("CREATE TEMP TABLE wanted(customer_id VARCHAR)")
        connection.executemany("INSERT INTO wanted VALUES (?)", [(item,) for item in ids])
        records = connection.execute(
            f"""
            SELECT t.transaction_id, t.customer_id, CAST(t.transaction_date AS VARCHAR), t.amount,
                   t.currency, t.merchant_name, t.transaction_type, t.transaction_status
            FROM {VIEW} t JOIN wanted USING (customer_id)
            ORDER BY t.customer_id, t.transaction_date DESC, t.transaction_id
            """
        ).fetchall()
    finally:
        connection.close()
    rows: dict[str, list[Row]] = {}
    for rid, cid, day, amount, currency, merchant, kind, status in records:
        rows.setdefault(cid, []).append(
            Row(rid, cid, day[:10], float(amount or 0), currency or "", merchant or UNNAMED, kind or "", status or "")
        )
    return rows


def eligible_customers(db_path: Path) -> list[str]:
    import duckdb

    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        found = connection.execute(
            f"SELECT customer_id FROM {VIEW} GROUP BY customer_id HAVING count(*) >= {MIN_CHARGES} ORDER BY customer_id"
        ).fetchall()
    finally:
        connection.close()
    return [item[0] for item in found]


def sample_customers(customers: list[str], sizes: dict[str, int], seed: int = SEED) -> dict[str, list[str]]:
    """A fixed sample of customers per split. Each customer belongs to one split by hash."""
    by_split: dict[str, list[str]] = {split: [] for split in SPLITS}
    for customer in customers:
        by_split[customer_split(customer)].append(customer)
    rng = random.Random(seed)
    return {split: sorted(rng.sample(pool, min(sizes[split], len(pool)))) for split, pool in by_split.items()}


# --- phrasing -------------------------------------------------------------


def _amount_text(row: Row, lang: str, rng: random.Random) -> tuple[str, bool]:
    value = row.amount
    whole = round(value)
    if rng.random() < 0.15 and 10 <= whole < 1_000_000_000:
        words = number_to_words(whole, lang)  # type: ignore[arg-type]
        return words, True
    cents = f"{value:.2f}"
    integer, fraction = cents.split(".")
    grouped_comma = f"{int(integer):,}"
    grouped_dot = grouped_comma.replace(",", ".")
    if lang == "pt":
        options = [f"R$ {grouped_dot},{fraction}", f"{grouped_dot},{fraction}", f"{integer},{fraction}", integer]
    else:
        options = [
            f"${grouped_comma}.{fraction}", f"{grouped_comma}.{fraction}", f"{grouped_dot},{fraction}",
            f"{integer}.{fraction}", integer, f"${integer}",
        ]
    if fraction == "00":
        options += [f"${grouped_comma}", f"{grouped_dot}"]
    return rng.choice(options), False


def _merchant_text(merchant: str, rng: random.Random) -> str:
    tokens = merchant.split()
    pick = rng.random()
    if pick < 0.45 or len(tokens) == 1 and pick < 0.7:
        text = merchant
    elif pick < 0.7 and len(tokens) > 1:
        text = " ".join(tokens[:2])
    else:
        longest = max(tokens, key=len)
        text = longest[: rng.choice((5, 6, 8))] if len(longest) > 6 else longest
    return text.lower() if rng.random() < 0.3 else text


def _date_text(target: str, today: str, lang: str, rng: random.Random) -> str:
    gap = (date.fromisoformat(today) - date.fromisoformat(target)).days
    day = date.fromisoformat(target)
    if gap == 0:
        return "hoy" if lang == "es" else "hoje"
    if gap == 1:
        return "ayer" if lang == "es" else "ontem"
    options = []
    if gap <= 6:
        weekday = _WEEKDAYS[lang][day.weekday()]
        options.append(f"el {weekday}" if lang == "es" else f"na {weekday}")
    options.append(f"hace {gap} días" if lang == "es" else f"há {gap} dias")
    month = _MONTHS[lang][day.month - 1]
    options.append(f"el {day.day} de {month}" if lang == "es" else f"dia {day.day} de {month}")
    return rng.choice(options)


def build_text(row: Row, today: str, locale: str, family: str, rng: random.Random) -> tuple[str, bool, bool]:
    """The description. Returns (text, mentions a merchant name, amount in words)."""
    lang = "es" if locale == "es-419" else "pt"
    named = row.merchant != UNNAMED
    pieces: dict[str, str] = {}
    in_words = False
    if rng.random() < 0.85:
        pieces["amount"], in_words = _amount_text(row, lang, rng)
    if rng.random() < 0.7:
        pieces["date"] = _date_text(row.date, today, lang, rng)
    mentions = named and rng.random() < 0.8
    if mentions:
        pieces["merchant"] = _merchant_text(row.merchant, rng)
    if row.kind in _TYPES[lang] and (not named and rng.random() < 0.6 or named and rng.random() < 0.2):
        pieces["type"] = _TYPES[lang][row.kind]
    if not pieces:
        pieces["amount"], in_words = _amount_text(row, lang, rng)
    opening, order, closing = _FAMILY[family][lang]
    words = [opening] if opening else []
    for item in order:
        slot, _, preposition = item.partition(":")
        if slot in pieces:
            words.append(f"{preposition} {pieces[slot]}".strip())
    if closing:
        words.append(closing)
    text = " ".join(words)
    text = text.replace(" ?", "?") if text.endswith("?") else text
    return text, mentions, in_words


def _gap_days(rng: random.Random) -> int:
    pick = rng.random()
    if pick < 0.2:
        return 0
    if pick < 0.4:
        return 1
    if pick < 0.7:
        return rng.randint(2, 7)
    return rng.randint(8, 30)


def build_examples(
    rows_by_customer: dict[str, list[Row]],
    per_customer: dict[str, int],
    seed: int = SEED,
    as_of: str = "2026-06-17",
) -> list[Example]:
    """Examples for the customers given. Same rows and seed give the same examples."""
    examples: list[Example] = []
    for customer_id in sorted(rows_by_customer):
        rows = rows_by_customer[customer_id]
        split = customer_split(customer_id)
        window = [row for row in rows if split_of_date(row.date) == split and row.date <= as_of]
        if not window:
            continue
        rng = random.Random(f"{seed}:{customer_id}")
        for index in range(per_customer[split]):
            target = rng.choice(window)
            today = min(date.fromisoformat(target.date) + timedelta(days=_gap_days(rng)), date.fromisoformat(as_of))
            family = rng.choice(FAMILIES if split == "test" else TRAIN_FAMILIES)
            locale = rng.choice(LOCALES)
            text, mentions, in_words = build_text(target, today.isoformat(), locale, family, rng)
            digest = hashlib.sha256(f"{seed}:{customer_id}:{target.transaction_id}:{index}".encode()).hexdigest()[:12]
            examples.append(
                Example(
                    f"CX-{digest}", customer_id, target.transaction_id, today.isoformat(), locale, family,
                    split, text, mentions, in_words,
                )
            )
    return examples


def digest_of(examples: list[Example]) -> str:
    """A hash of the examples, in canonical order. It proves that a rebuild gives the same set."""
    body = "\n".join(json.dumps(asdict(item), sort_keys=True, ensure_ascii=False) for item in examples)
    return hashlib.sha256(body.encode()).hexdigest()
