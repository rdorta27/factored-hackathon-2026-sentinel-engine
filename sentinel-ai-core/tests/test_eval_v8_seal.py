"""v8 seal guards: draft schema and the unchanged v7 entry (eval-v8 task 2.4)."""

import json
from pathlib import Path

from eval.cases import validate_case

HERE = Path(__file__).parent.parent
V7_HASH = "27ad2f1ba986b80473e9cf37d8945734e360ed022058f165d84921ba4293d5af"


def _draft_rows():
    path = HERE / "eval" / "cases" / "sealed_v8" / "intent-draft.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_v8_intent_draft_covers_four_variants():
    from collections import Counter

    rows = _draft_rows()
    assert len(rows) == 192
    assert dict(Counter(r["variant"] for r in rows)) == {
        "es-MX": 48, "es-CO": 48, "es-AR": 48, "pt-BR": 48,
    }
    assert len({r["base_id"] for r in rows}) == 48
    for index, row in enumerate(rows):
        validate_case(row, f"sealed_v8/intent-draft.jsonl:{index}")


def test_v7_seal_and_measurement_stay_unchanged():
    seal = json.loads((HERE / "eval" / "cases" / "seal.json").read_text(encoding="utf-8"))
    assert seal["hash"] == V7_HASH
    measured = json.loads((HERE / "eval" / "measured.json").read_text(encoding="utf-8"))
    assert measured["measured"] == [{"hash": V7_HASH, "run_id": "2024Q4-eval-v7"}]


def test_staging_is_not_the_seal():
    from eval.seal import content_hash, verify_seal

    record = verify_seal(HERE / "eval" / "cases" / "sealed", HERE / "eval" / "cases" / "seal.json")
    assert record["hash"] == V7_HASH
    assert (HERE / "eval" / "cases" / "sealed_v8" / "seal.json").exists() is False
    assert content_hash(HERE / "eval" / "cases" / "sealed_v8") != V7_HASH
