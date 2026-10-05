"""Build and freeze the splits of the charge selector (run data-v1).

Reads the local Gold file and writes aggregates only: counts, hashes, the seed
and the family list. It writes no rows and no customer ids. A run is
write-once, so the script refuses to write into an existing folder.

    SENTINEL_GOLD_DUCKDB=<path> python -m eval.build_charge_splits
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

from eval import charge_examples as gen

RUN = Path(__file__).resolve().parents[2] / "evidence" / "charge-ranker" / "data-v1"
SOURCES = (Path(gen.__file__), Path(gen.__file__).parents[1] / "app" / "ai" / "number_words.py")


def _hash(values: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(values)).encode()).hexdigest()


def summarize(examples: list[gen.Example], rows: dict[str, list[gen.Row]]) -> dict:
    by_split = {split: [item for item in examples if item.split == split] for split in gen.SPLITS}
    customers = {split: {item.customer_id for item in items} for split, items in by_split.items()}
    by_id = {row.transaction_id: row for items in rows.values() for row in items}
    splits = {}
    for split, items in by_split.items():
        sizes = [len(gen.pool_of(item, rows)) for item in items]
        dates = [by_id[item.target_id].date for item in items]
        splits[split] = {
            "examples": len(items),
            "customers": len(customers[split]),
            "customers_hash": _hash(sorted(customers[split])),
            "target_date_first": min(dates),
            "target_date_last": max(dates),
            "families": {name: sum(i.family == name for i in items) for name in gen.FAMILIES},
            "locales": {name: sum(i.locale == name for i in items) for name in gen.LOCALES},
            "mentions_merchant": sum(i.has_merchant for i in items),
            "amount_in_words": sum(i.amount_in_words for i in items),
            "candidates_median": statistics.median(sizes),
            "candidates_max": max(sizes),
        }
    shared = sum(
        len(customers[a] & customers[b]) for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))
    )
    test_only = sum(
        1 for item in examples if item.family in gen.TEST_ONLY_FAMILIES and item.split != "test"
    )
    return {
        "run": "charge-ranker/data-v1",
        "data_type": "Simulation: team-generated descriptions of real Gold transactions. Labels are exact.",
        "seed": gen.SEED,
        "families": {"train": list(gen.TRAIN_FAMILIES), "test_only": list(gen.TEST_ONLY_FAMILIES)},
        "split_rule": {
            "customers": {name: list(span) for name, span in gen.CUSTOMER_SHARE.items()},
            "target_dates": gen.DATE_RANGE,
        },
        "customers_per_split": gen.CUSTOMERS_PER_SPLIT,
        "examples_per_customer": gen.EXAMPLES_PER_CUSTOMER,
        "splits": splits,
        "checks": {"customers_in_two_splits": shared, "test_only_families_outside_test": test_only},
        "examples_hash": gen.digest_of(examples),
        "code_hash": hashlib.sha256(b"".join(path.read_bytes() for path in SOURCES)).hexdigest(),
    }


def main() -> None:
    if RUN.exists():
        raise SystemExit(f"{RUN} exists. A run is write-once: use a new folder name.")
    examples, rows = gen.build_dataset(gen.gold_path())
    summary = summarize(examples, rows)
    if summary["checks"] != {"customers_in_two_splits": 0, "test_only_families_outside_test": 0}:
        raise SystemExit(f"split checks failed: {summary['checks']}")
    RUN.mkdir(parents=True)
    (RUN / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary["splits"], indent=1), file=sys.stderr)


if __name__ == "__main__":
    main()
