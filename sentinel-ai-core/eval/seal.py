"""Seal the held-out set by hash before it is measured, and record each measurement.

Usage from ``sentinel-ai-core/``::

    python3 -m eval.seal --author "<name>"

Sealing refuses an undersized set and writes ``eval/cases/seal.json`` with the
content hash, the counts and the author. ``eval/measured.json`` is append-only:
it lists every seal hash already measured, so the same sealed set is never
measured twice (REQ-0017, REQ-0020, decision 018).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from eval.cases import INTENTS, VARIANTS, Case, load_dir

HERE = Path(__file__).parent
SEALED_DIR = HERE / "cases" / "sealed"
SEAL_PATH = HERE / "cases" / "seal.json"
MEASURED_PATH = HERE / "measured.json"


@dataclass(frozen=True)
class Minimums:
    bases: int = 70
    per_intent: int = 25
    noisy: int = 50
    attacks: int = 75


class SealRefused(ValueError):
    """The set is undersized, edited after sealing, or already measured."""


def content_hash(directory: Path | str = SEALED_DIR) -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(directory).glob("*.jsonl")):
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def blocks(cases: list[Case]) -> dict[str, list[Case]]:
    held = [c for c in cases if c.split == "held_out"]
    return {
        "main": [c for c in held if "noisy" not in c.tags and "adversarial" not in c.tags],
        "noisy": [c for c in held if "noisy" in c.tags],
        "attacks": [c for c in held if "adversarial" in c.tags],
    }


def shortfalls(cases: list[Case], minimums: Minimums = Minimums()) -> list[str]:
    parts = blocks(cases)
    main = parts["main"]
    problems = []
    variants_by_base: dict[str, set[str]] = {}
    for case in main:
        if case.base_id is None or case.variant is None:
            problems.append(f"case {case.id} has no base_id or variant")
            continue
        variants_by_base.setdefault(case.base_id, set()).add(case.variant)
    if len(variants_by_base) < minimums.bases:
        problems.append(f"{len(variants_by_base)} bases, need {minimums.bases}")
    for base, seen in sorted(variants_by_base.items()):
        missing = sorted(set(VARIANTS) - seen)
        if missing:
            problems.append(f"base {base} lacks variants {missing}")
    intents = Counter(c.expected_intent for c in main)
    for intent in INTENTS:
        if intents[intent] < minimums.per_intent:
            problems.append(f"intent {intent} has {intents[intent]} cases, need {minimums.per_intent}")
    main_keys = {(c.base_id, c.variant) for c in main}
    for case in parts["noisy"]:
        if (case.base_id, case.variant) not in main_keys:
            problems.append(f"noisy case {case.id} references no sealed base {case.base_id} {case.variant}")
    if len(parts["noisy"]) < minimums.noisy:
        problems.append(f"{len(parts['noisy'])} noisy twins, need {minimums.noisy}")
    if len(parts["attacks"]) < minimums.attacks:
        problems.append(f"{len(parts['attacks'])} attacks, need {minimums.attacks}")
    return problems


def seal(
    author: str,
    directory: Path | str = SEALED_DIR,
    seal_path: Path | str = SEAL_PATH,
    minimums: Minimums = Minimums(),
    today: str | None = None,
) -> dict:
    if not author.strip():
        raise SealRefused("the seal needs the author of the held-out cases")
    cases = load_dir(directory)
    problems = shortfalls(cases, minimums)
    if problems:
        raise SealRefused("sealing refused: " + "; ".join(problems))
    parts = blocks(cases)
    record = {
        "hash": content_hash(directory),
        "files": sorted(p.name for p in Path(directory).glob("*.jsonl")),
        "n": len(cases),
        "bases": len({c.base_id for c in parts["main"]}),
        "by_variant": dict(sorted(Counter(c.variant for c in parts["main"]).items())),
        "by_intent": dict(sorted(Counter(c.expected_intent for c in parts["main"]).items())),
        "noisy": len(parts["noisy"]),
        "attacks": len(parts["attacks"]),
        "sealed_on": today or date.today().isoformat(),
        "author": author.strip(),
    }
    Path(seal_path).write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def verify_seal(directory: Path | str = SEALED_DIR, seal_path: Path | str = SEAL_PATH) -> dict:
    path = Path(seal_path)
    if not path.is_file():
        raise SealRefused(f"no seal record at {path}; seal the held-out set first")
    record = json.loads(path.read_text(encoding="utf-8"))
    current = content_hash(directory)
    if current != record.get("hash"):
        raise SealRefused(f"sealed set changed after sealing: hash {current[:16]} != {str(record.get('hash'))[:16]}")
    return record


def _measured(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return list(json.loads(path.read_text(encoding="utf-8")).get("measured", []))


def assert_not_measured(seal_hash: str, measured_path: Path | str = MEASURED_PATH) -> None:
    for entry in _measured(Path(measured_path)):
        if entry.get("hash") == seal_hash:
            raise SealRefused(f"sealed set {seal_hash[:16]} was already measured in run {entry.get('run_id')}")


def record_measured(seal_hash: str, run_id: str, measured_path: Path | str = MEASURED_PATH) -> None:
    path = Path(measured_path)
    assert_not_measured(seal_hash, path)
    entries = _measured(path) + [{"hash": seal_hash, "run_id": run_id}]
    path.write_text(json.dumps({"measured": entries}, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seal the held-out set by hash.")
    parser.add_argument("--author", required=True, help="who wrote the held-out cases")
    record = seal(parser.parse_args().author)
    print(f"[seal] {record['n']} cases, {record['bases']} bases, hash {record['hash'][:16]}")


if __name__ == "__main__":
    main()


__all__ = [
    "Minimums",
    "SealRefused",
    "assert_not_measured",
    "blocks",
    "content_hash",
    "record_measured",
    "seal",
    "shortfalls",
    "verify_seal",
]
