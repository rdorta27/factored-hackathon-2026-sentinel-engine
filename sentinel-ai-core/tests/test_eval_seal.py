"""Sealing the held-out set: sizes, hash check and single measurement."""

import json
from pathlib import Path

import pytest

from eval.seal import (
    Minimums,
    SealRefused,
    assert_not_measured,
    record_measured,
    seal,
    verify_seal,
)

VARIANT_FIELDS = {
    "es-MX": ("es-419", "MX"),
    "es-CO": ("es-419", "CO"),
    "es-AR": ("es-419", "AR"),
    "pt-BR": ("pt-BR", "MX"),
}
SMALL = Minimums(bases=2, per_intent=2, noisy=1, attacks=1)


def _row(case_id: str, base: str, variant: str, intent: str = "charge", **extra) -> dict:  # type: ignore[no-untyped-def]
    locale, country = VARIANT_FIELDS[variant]
    row = {
        "id": case_id, "locale": locale, "country": country, "turns": [f"texto {case_id}"],
        "expected_intent": intent, "expected_outcome": "clarification", "split": "held_out",
        "base_id": base, "variant": variant,
    }
    row.update(extra)
    return row


def _write(folder: Path, bases: int = 2, with_noisy: bool = True, with_attack: bool = True) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for b in range(bases):
        intent = ("charge", "status", "missing", "out_of_scope", "person")[b % 5]
        for variant in VARIANT_FIELDS:
            rows.append(_row(f"b{b}-{variant}", f"b{b}", variant, intent))
    if with_noisy:
        rows.append(_row("n-1", "b0", "es-MX", tags=["noisy"], perturbation="amount_shift"))
    if with_attack:
        rows.append({**_row("a-1", "a0", "es-MX"), "tags": ["adversarial"], "must_not_pass": True})
    (folder / "held_out.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )


def test_undersized_set_is_refused_naming_the_shortfall(tmp_path: Path) -> None:
    _write(tmp_path / "sealed", bases=1, with_noisy=False)
    with pytest.raises(SealRefused) as error:
        seal("Ana", tmp_path / "sealed", tmp_path / "seal.json", SMALL)
    message = str(error.value)
    assert "1 bases, need 2" in message
    assert "noisy twins" in message
    assert not (tmp_path / "seal.json").exists()


def test_intent_below_minimum_is_refused(tmp_path: Path) -> None:
    _write(tmp_path / "sealed", bases=3)
    with pytest.raises(SealRefused, match="intent out_of_scope has 0 cases"):
        seal("Ana", tmp_path / "sealed", tmp_path / "seal.json", Minimums(bases=3, per_intent=1, noisy=1, attacks=1))


def test_seal_records_hash_counts_and_author(tmp_path: Path) -> None:
    _write(tmp_path / "sealed", bases=5)
    record = seal("Ana", tmp_path / "sealed", tmp_path / "seal.json", SMALL, today="2026-10-02")
    assert record["bases"] == 5
    assert record["by_variant"] == {"es-AR": 5, "es-CO": 5, "es-MX": 5, "pt-BR": 5}
    assert (record["noisy"], record["attacks"], record["author"]) == (1, 1, "Ana")
    assert verify_seal(tmp_path / "sealed", tmp_path / "seal.json")["hash"] == record["hash"]


def test_edited_sealed_file_fails_the_hash_check(tmp_path: Path) -> None:
    _write(tmp_path / "sealed", bases=5)
    seal("Ana", tmp_path / "sealed", tmp_path / "seal.json", SMALL)
    path = tmp_path / "sealed" / "held_out.jsonl"
    path.write_text(path.read_text(encoding="utf-8").replace("texto b0", "texto editado"), encoding="utf-8")
    with pytest.raises(SealRefused, match="changed after sealing"):
        verify_seal(tmp_path / "sealed", tmp_path / "seal.json")


def test_a_sealed_hash_is_measured_once(tmp_path: Path) -> None:
    measured = tmp_path / "measured.json"
    record_measured("abc123", "2024Q4-eval-v7", measured)
    with pytest.raises(SealRefused, match="2024Q4-eval-v7"):
        assert_not_measured("abc123", measured)
    with pytest.raises(SealRefused):
        record_measured("abc123", "2024Q4-eval-v8", measured)
    assert json.loads(measured.read_text())["measured"] == [{"hash": "abc123", "run_id": "2024Q4-eval-v7"}]
