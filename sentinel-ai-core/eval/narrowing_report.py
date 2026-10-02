"""Offline narrowing report for the MT-06 development cases.

No model call: exact and soft facts run against the mock Gold rows. "Before"
is the old list (newest four, never a not-found key). "After" is
`narrow_candidates`. Right-charge-shown means the shown ids equal the expected
ids; a not-found case expects the newest four.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.ai.grounding import extract_facts, extract_soft, narrow_candidates
from app.tools.gold import MockGoldStore, to_candidate

REFERENCE = date(2026, 6, 17)
SHOWN = 4
CASES = Path(__file__).parent / "cases" / "narrowing" / "mt06.jsonl"


def _rows():
    return [to_candidate(row) for row in MockGoldStore(as_of="2026-06-17").list_for_customer("CUST-0001")]


def _newest(rows) -> list[str]:
    return [row.candidate_id for row in sorted(rows, key=lambda row: row.date, reverse=True)[:SHOWN]]


def load_rows() -> list[dict]:
    return [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]


def score(body: dict, rows, *, narrowed: bool) -> tuple[bool, bool]:
    message = body["turns"][0]
    merchants = [row.merchant for row in rows]
    expected = list(body["expected_charge_ids"])
    if not expected:
        expected = _newest(rows)
    if narrowed:
        facts = extract_facts(message, REFERENCE.year, merchants)
        soft = extract_soft(message, REFERENCE, merchants)
        result = narrow_candidates(facts, soft, rows, REFERENCE)
        shown = [row.candidate_id for row in result.candidates[:SHOWN]]
        said = result.not_found
    else:
        shown = _newest(rows)
        said = False
    return shown == expected, said == bool(body["expect_not_found"])


def report() -> dict:
    rows = _rows()
    bodies = load_rows()
    before = [score(body, rows, narrowed=False) for body in bodies]
    after = [score(body, rows, narrowed=True) for body in bodies]
    n = len(bodies)

    def rate(pairs: list[tuple[bool, bool]], index: int) -> str:
        hits = sum(1 for pair in pairs if pair[index])
        return f"{hits}/{n}"

    return {
        "n": n,
        "before": {"right_charge_shown": rate(before, 0), "not_found_said": rate(before, 1)},
        "after": {"right_charge_shown": rate(after, 0), "not_found_said": rate(after, 1)},
    }


def main() -> None:
    print(json.dumps(report(), indent=2))


if __name__ == "__main__":
    main()
