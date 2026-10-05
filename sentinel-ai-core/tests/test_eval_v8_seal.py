"""v8 seal guards: draft schema and the unchanged v7 entry (eval-v8 task 2.4)."""

import json
from pathlib import Path

from eval.cases import validate_case

HERE = Path(__file__).parent.parent
V7_HASH = "27ad2f1ba986b80473e9cf37d8945734e360ed022058f165d84921ba4293d5af"


def _intent_rows():
    path = HERE / "eval" / "cases" / "sealed_v8" / "intent.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_v8_intent_block_covers_four_variants():
    from collections import Counter

    rows = _intent_rows()
    assert len(rows) == 212
    assert dict(Counter(r["variant"] for r in rows)) == {
        "es-MX": 53, "es-CO": 53, "es-AR": 53, "pt-BR": 53,
    }
    assert len({r["base_id"] for r in rows}) == 53
    for index, row in enumerate(rows):
        validate_case(row, f"sealed_v8/intent.jsonl:{index}")


def test_v7_seal_and_measurement_stay_unchanged():
    seal = json.loads((HERE / "eval" / "cases" / "seal.json").read_text(encoding="utf-8"))
    assert seal["hash"] == V7_HASH
    measured = json.loads((HERE / "eval" / "measured.json").read_text(encoding="utf-8"))
    assert measured["measured"] == [{"hash": V7_HASH, "run_id": "2024Q4-eval-v7"}]


def test_v8_seal_verifies_and_uses_no_measurement():
    import json as _json

    from eval.seal import assert_not_measured, verify_seal

    record = verify_seal(HERE / "eval" / "cases" / "sealed_v8", HERE / "eval" / "cases" / "sealed_v8" / "seal.json")
    assert record["n"] == 444
    assert record["hash"] != V7_HASH
    assert_not_measured(record["hash"], HERE / "eval" / "measured.json")
    measured = _json.loads((HERE / "eval" / "measured.json").read_text(encoding="utf-8"))
    assert measured["measured"] == [{"hash": V7_HASH, "run_id": "2024Q4-eval-v7"}]


def test_v8_seal_covers_four_complete_blocks():
    from eval.cases import load_dir
    from eval.seal import blocks, shortfalls

    assert shortfalls(load_dir(HERE / "eval" / "cases" / "sealed_v8")) == []
    parts = blocks(load_dir(HERE / "eval" / "cases" / "sealed_v8"))
    assert len(parts["main"]) == 308
    assert len(parts["noisy"]) == 52
    assert len(parts["attacks"]) == 84
