"""A learned selector that ranks the charges of the session customer (decision 025).

For one description and one charge, `clues` gives a short list of numbers. The
model adds them with weights and ranks the charges. The clues call the parsers
of `app/ai/grounding.py`. The selector adds weights and replaces no parser.

The weights file holds numbers only. The service loads it only when its hash
equals the hash that the run recorded. This module never imports training code.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.ai.grounding import (
    MONTHS,
    extract_facts,
    is_repeated_charge,
    normalize_amount,
    normalize_text,
    parse_amount,
    parse_date,
    relative_dates,
    shares_prefix,
    stated_merchant_tokens,
    token_matches_merchant,
    _content_tokens,
)
from app.ai.number_words import is_number_word, words_to_numbers
from app.orchestrator.types import Candidate, TransactionStatus

FEATURES = (
    "amount_exact", "amount_close", "amount_mismatch", "words_match", "words_mismatch",
    "merchant_exact", "merchant_soft_all", "merchant_soft_fraction", "merchant_prefix",
    "merchant_mismatch", "unnamed", "unnamed_when_merchant_stated", "named_not_mentioned",
    "date_exact", "date_mismatch", "date_gap", "age_log", "age_unstated", "age_le_3", "newest",
    "rank_fraction", "repeated_pair", "approved", "matched_kinds", "contradictions",
)
UNNAMED = "unspecified"
_MONTH_WORDS = "|".join(sorted(MONTHS, key=len, reverse=True))
_DATE_PHRASES = re.compile(
    rf"\b\d{{1,2}}\s*(?:de\s+)?(?:{_MONTH_WORDS})\b|\b\d{{4}}-\d{{2}}-\d{{2}}\b|"
    r"\b(?:hace|ha|faz)\s+\d+\s+dias?\b"
)


def is_unnamed(merchant: str) -> bool:
    return not merchant.strip() or normalize_text(merchant) == UNNAMED


@dataclass(frozen=True)
class Description:
    """What one customer text states, read once for every charge."""

    amount: float | None
    words: tuple[int, ...]
    merchant: str | None
    tokens: tuple[str, ...]
    dates: frozenset[str]
    repeated: bool

    @property
    def merchant_stated(self) -> bool:
        return bool(self.merchant or self.tokens)

    @property
    def stated(self) -> bool:
        return bool(self.amount or self.words or self.merchant_stated or self.dates)


def read_description(text: str, today: date, merchants: list[str]) -> Description:
    named = [merchant for merchant in merchants if not is_unnamed(merchant)]
    normalized = normalize_text(text)
    stripped = _DATE_PHRASES.sub(" ", normalized)
    amount_text = parse_amount(stripped)
    dates = set(relative_dates(text, today))
    absolute = _absolute_date(normalized, today)
    if absolute:
        dates.add(absolute)
    facts = extract_facts(text, today.year, named)
    return Description(
        amount=float(amount_text) if amount_text else None,
        words=tuple(words_to_numbers(text)),
        merchant=facts.merchant,
        tokens=tuple(token for token in stated_merchant_tokens(text, named) if not is_number_word(token)),
        dates=frozenset(dates),
        repeated=is_repeated_charge(text),
    )


def _absolute_date(normalized: str, today: date) -> str | None:
    """A stated day and month, as the most recent such date on or before today."""
    parsed = parse_date(normalized, today.year)
    if parsed is None:
        return None
    try:
        found = date.fromisoformat(parsed)
        if found > today:
            found = found.replace(year=today.year - 1)
    except ValueError:
        return None
    return found.isoformat()


def _close(left: float, right: float) -> float:
    return abs(left - right) / max(left, right, 1e-9)


def _day_gap(first: str, second: str) -> int:
    return abs((date.fromisoformat(first) - date.fromisoformat(second)).days)


def clues(description: Description, row: Candidate, pool: list[Candidate], today: date) -> list[float]:
    """The numbers for one charge. `pool` is every charge listed, newest first."""
    value = float(normalize_amount(row.amount) or 0)
    unnamed = is_unnamed(row.merchant)
    amount_exact = amount_close = amount_mismatch = 0.0
    if description.amount is not None:
        gap = _close(description.amount, value)
        amount_exact = float(normalize_amount(row.amount) == f"{description.amount:.2f}")
        amount_close = max(0.0, 1.0 - min(gap * 20, 1.0))
        amount_mismatch = float(gap > 0.02)
    words_match = words_mismatch = 0.0
    if description.words:
        hit = any(abs(number - round(value)) <= 1 or _close(number, value) < 0.001 for number in description.words)
        words_match, words_mismatch = float(hit), float(not hit)
    exact = soft_all = 0.0
    fraction = prefix = 0.0
    if not unnamed:
        exact = float(bool(description.merchant) and normalize_text(row.merchant) == normalize_text(description.merchant))
        if description.tokens:
            hits = [token_matches_merchant(token, row.merchant) for token in description.tokens]
            soft_all = float(all(hits))
            fraction = sum(hits) / len(hits)
            parts = _content_tokens(row.merchant)
            best = max(
                (sum(1 for a, b in zip(token, part) if a == b) if shares_prefix(token, part, 1) else 0)
                for token in description.tokens for part in parts
            ) if parts else 0
            prefix = min(best, 8) / 8
    merchant_ok = bool(exact or soft_all)
    merchant_mismatch = float(description.merchant_stated and not merchant_ok)
    date_exact = date_mismatch = date_gap = 0.0
    if description.dates:
        date_exact = float(row.date in description.dates)
        date_mismatch = float(not date_exact)
        date_gap = min(min(_day_gap(row.date, item) for item in description.dates), 30) / 30
    try:
        age = max((today - date.fromisoformat(row.date)).days, 0)
    except ValueError:
        age = 1000
    age_log = math.log1p(age) / math.log1p(1000)
    index = next((i for i, item in enumerate(pool) if item.candidate_id == row.candidate_id), 0)
    pair = (normalize_text(row.merchant), normalize_amount(row.amount))
    same = sum(1 for item in pool if (normalize_text(item.merchant), normalize_amount(item.amount)) == pair)
    kinds = [
        bool(amount_exact or words_match or (description.amount is not None and amount_close > 0.9)),
        merchant_ok,
        bool(date_exact),
    ]
    stated = [
        description.amount is not None or bool(description.words),
        description.merchant_stated,
        bool(description.dates),
    ]
    matched = sum(1 for hit, said in zip(kinds, stated) if hit and said)
    contradictions = sum(1 for hit, said in zip(kinds, stated) if said and not hit)
    return [
        amount_exact, amount_close, amount_mismatch, words_match, words_mismatch,
        exact, soft_all, fraction, prefix, merchant_mismatch, float(unnamed),
        float(unnamed and description.merchant_stated), float(not unnamed and not description.merchant_stated),
        date_exact, date_mismatch, date_gap, age_log, 0.0 if description.stated else age_log,
        float(age <= 3), float(index == 0), index / max(len(pool), 1),
        float(description.repeated and same >= 2), float(row.status == TransactionStatus.APPROVED),
        matched / 3, contradictions / 3,
    ]


def feature_matrix(text: str, pool: list[Candidate], today: date) -> list[list[float]]:
    """One row of clues per charge of `pool`, in the order of `pool`."""
    ordered = sorted(pool, key=lambda row: row.date, reverse=True)
    description = read_description(text, today, [row.merchant for row in ordered])
    by_id = {row.candidate_id: clues(description, row, ordered, today) for row in ordered}
    return [by_id[row.candidate_id] for row in pool]


def softmax_top(scores: list[float], temperature: float) -> float:
    peak = max(scores)
    weights = [math.exp((score - peak) / temperature) for score in scores]
    return 1.0 / sum(weights) if weights else 0.0


@dataclass(frozen=True)
class Ranking:
    ordered: list[Candidate]
    confidence: float
    pick: Candidate | None


class RankerHashMismatch(RuntimeError):
    """The weights file differs from the hash that the run recorded."""


@dataclass(frozen=True)
class ChargeRanker:
    weights: tuple[float, ...]
    temperature: float
    threshold: float

    def scores(self, rows: list[list[float]]) -> list[float]:
        return [sum(w * x for w, x in zip(self.weights, row)) for row in rows]

    def rank(self, text: str, pool: list[Candidate], today: date) -> Ranking:
        if not pool:
            return Ranking([], 0.0, None)
        scores = self.scores(feature_matrix(text, pool, today))
        order = sorted(range(len(pool)), key=lambda i: -scores[i])
        ordered = [pool[i] for i in order]
        confidence = softmax_top([scores[i] for i in order], self.temperature)
        pick = ordered[0] if confidence >= self.threshold else None
        return Ranking(ordered, confidence, pick)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_ranker(model_path: Path, expected_sha256: str) -> ChargeRanker:
    """Load the weights. Refuse a file whose hash differs from the recorded one."""
    actual = file_hash(model_path)
    if actual != expected_sha256:
        raise RankerHashMismatch(f"model file hash {actual[:12]} differs from the run hash {expected_sha256[:12]}")
    body = json.loads(model_path.read_text(encoding="utf-8"))
    if tuple(body["features"]) != FEATURES:
        raise RankerHashMismatch("the clue list of the model differs from the clue list of the code")
    return ChargeRanker(tuple(body["weights"]), float(body["temperature"]), float(body["threshold"]))
