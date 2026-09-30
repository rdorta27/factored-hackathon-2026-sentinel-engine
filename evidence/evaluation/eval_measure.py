#!/usr/bin/env python3
"""Evaluation evidence for the runner (labels, mix, thresholds).

Freezes what the evaluation runner consumes: the label universe
(category x subcategory), the Claim case mix, claimed-amount percentiles,
label-quality checks, the intent mix and the amount/fraud reference
thresholds. Flow evidence chose the flow; this evidence feeds the runner.

Stdlib only. Reads the gitignored dataset, writes aggregates only.

Usage:
    python3 eval_measure.py run [RUN_ID] [WINDOW]
    python3 eval_measure.py verify [RUN_ID]
    python3 eval_measure.py derive [RUN_ID]
    python3 eval_measure.py --help
    RUN_ID like 2024Q4-v1 (default). WINDOW like 2024Q4 (dev zone).
    Held-out cut 2025-07-01: development < cut, held-out >= cut.
    Only the development window is read; held-out rows are excluded.
"""

import csv
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter

SCRIPT_VERSION = "2026-09-30+eval-v1"
RESULTS: dict = {}

HELD_OUT_CUT = "2025-07-01"

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_CANDIDATES = [
    os.path.join(BASE, "data"),
    os.path.join(os.path.dirname(BASE), "data"),
]


def find_data() -> str:
    for candidate in DATA_CANDIDATES:
        if os.path.isdir(candidate):
            return candidate
    raise SystemExit(
        "no dataset found: expected evidence/evaluation/data/ "
        "(gitignored symlink to the synced data tree) or evidence/data/; "
        "sync from S3 first, rows never enter the repository"
    )


DATA = None  # resolved lazily so --help works without data

WINDOW_DEFAULT = "2024Q4"
RUN_ID_DEFAULT = "2024Q4-v1"


def window_bounds(window: str) -> tuple[str, str]:
    match = re.fullmatch(r"(\d{4})Q([1-4])", window)
    if not match:
        raise SystemExit(f"WINDOW must look like 2024Q4, got {window!r}")
    year, quarter = int(match.group(1)), int(match.group(2))
    first_month = 3 * quarter - 2
    end_month = first_month + 3
    end_year = year + (1 if end_month > 12 else 0)
    end_month = end_month - 12 if end_month > 12 else end_month
    return f"{year}-{first_month:02d}-01", f"{end_year}-{end_month:02d}-01"


def record(mode: str, key: str, value):  # type: ignore[no-untyped-def]
    """Store a machine-readable metric for the run mode."""
    RESULTS.setdefault(mode, {})[key] = value


def scan(pattern: str, data_dir: str, encoding: str = "utf-8-sig"):  # type: ignore[no-untyped-def]
    """Yield cleaned rows from all CSVs matching a glob under data/."""
    files = sorted(glob.glob(os.path.join(data_dir, pattern)))
    if not files:
        raise SystemExit(f"no files match data/{pattern} -- sync from S3 first")
    dropped = 0
    for path in files:
        with open(path, newline="", encoding=encoding) as handle:
            for row in csv.DictReader(handle):
                clean = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                if not any(clean.values()):
                    dropped += 1
                    continue
                yield clean
    print(f"[scan] {len(files)} files under data/{pattern} (dropped {dropped} fully-empty rows)")


def in_window(rows, event_col: str, start: str, end: str, label: str = ""):  # type: ignore[no-untyped-def]
    """Keep rows whose event date falls inside [start, end)."""
    kept, out = [], 0
    for row in rows:
        day = (row.get(event_col) or "")[:10]
        if start <= day < end:
            kept.append(row)
        else:
            out += 1
    print(f"[window{label}] event {event_col} in [{start}, {end}): kept {len(kept)}, excluded {out}")
    return kept


def value_counts(rows, *cols: str, limit: int = 15):  # type: ignore[no-untyped-def]
    """Count distinct value combos of cols over an iterable of rows."""
    counter: Counter = Counter()
    total = 0
    for row in rows:
        total += 1
        counter[tuple((row.get(col) or "").strip() for col in cols)] += 1
    if total == 0:
        print("[counts] n=0 (empty input -- check filters)")
        return 0, counter
    print(f"[counts] n={total} distinct={len(counter)}")
    for key, value in counter.most_common(limit):
        print(f"  {value:7d} ({value / total * 100:5.2f}%)  {key}")
    if len(counter) > limit:
        rest = sum(v for _, v in counter.most_common()[limit:])
        print(f"  ... {len(counter) - limit} more combos ({rest} rows)")
    return total, counter


def date_guard(rows, date_cols: list[str], label: str = "") -> int:  # type: ignore[no-untyped-def]
    """Count rows reaching the held-out zone (>= HELD_OUT_CUT)."""
    bad = total = 0
    for row in rows:
        total += 1
        for col in date_cols:
            value = (row.get(col) or "").strip()[:10]
            if value >= HELD_OUT_CUT:
                bad += 1
                break
    print(f"[date-guard{label}] n={total} rows at/after {HELD_OUT_CUT}: {bad}")
    return bad


def percentiles(values: list[float], points: tuple = (50, 90, 95, 99)) -> dict:
    clean = sorted(v for v in values if v is not None)
    if not clean:
        return {f"p{p}": None for p in points}
    out = {}
    for point in points:
        rank = (point / 100) * (len(clean) - 1)
        low, high = int(rank), min(int(rank) + 1, len(clean) - 1)
        frac = rank - low
        out[f"p{point}"] = round(clean[low] + (clean[high] - clean[low]) * frac, 2)
    return out


def to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


_ID_LIKE = re.compile(r"CUST-\d|@|\b\d{7,}\b|[A-Z]{2,}\d{5,}")


def guard_summary(summary: dict) -> None:
    """Reject any output value shaped like an identifier or personal data."""
    def walk(node, path: str = "$"):  # type: ignore[no-untyped-def]
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(key, str) and _ID_LIKE.search(key):
                    raise SystemExit(f"guard: identifier-like key at {path}.{key}")
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{path}[{index}]")
        elif isinstance(node, str):
            if _ID_LIKE.search(node):
                raise SystemExit(f"guard: identifier-like value at {path}: {node[:32]!r}")

    walk(summary)
    print("[guard] aggregates only, no identifier-shaped values")


COMPLAINT_MONTH_PATS = ("complaints/year={y}/month={m:02d}/day=*/*.csv",)
INTERACTION_PATS = (
    "windows/{w}/interactions/*/*.csv",
    "windows/{w}/interactions/day=*/*.csv",
)
TRANSACTION_PATS = (
    "windows/{w}/transactions/*/*.csv",
    "windows/{w}/transactions/day=*/*.csv",
)
SNAPSHOT_PRODUCTS = "snapshots/products.csv"


def iter_patterns(patterns: tuple, data_dir: str, **fmt):  # type: ignore[no-untyped-def]
    rows = None
    for template in patterns:
        try:
            rows = list(scan(template.format(**fmt), data_dir))
            return rows
        except SystemExit:
            continue
    raise SystemExit(f"no files match any of {patterns} -- sync from S3 first")


def compute_summary(data_dir: str, window: str) -> dict:
    start, end = window_bounds(window)
    year, quarter = int(window[:4]), int(window[5])
    first_month = 3 * quarter - 2

    # --- complaints: window slice + full history for the global taxonomy ---
    window_rows = []
    months_found = 0
    for month in range(first_month, first_month + 3):
        try:
            window_rows.extend(
                scan(f"complaints/year={year}/month={month:02d}/day=*/*.csv", data_dir)
            )
            months_found += 1
        except SystemExit as exc:
            print(f"[scan] month {year}-{month:02d} missing ({exc}); continuing")
    if months_found == 0:
        raise SystemExit("no complaint files for the window -- sync from S3 first")
    window_rows = in_window(window_rows, "creation_date", start, end, ":complaints")
    held_out_rows = date_guard(window_rows, ["creation_date", "process_date"], ":complaints")
    if held_out_rows:
        raise SystemExit(f"held-out contamination: {held_out_rows} rows at/after {HELD_OUT_CUT}")

    history_rows = window_rows
    try:
        history_rows = list(scan("complaints/year=*/month=*/day=*/*.csv", data_dir))
    except SystemExit:
        pass

    def combo_counter(rows, case_type: str | None):  # type: ignore[no-untyped-def]
        selected = rows if case_type is None else [r for r in rows if (r.get("case_type") or "") == case_type]
        counter: Counter = Counter()
        for row in selected:
            counter[((row.get("category") or ""), (row.get("subcategory") or ""))] += 1
        total = sum(counter.values()) or 1
        return {
            f"{cat} || {sub}": {"count": count, "share": round(count / total, 4)}
            for (cat, sub), count in sorted(counter.items())
        }, sum(counter.values())

    claim_labels, claim_n = combo_counter(window_rows, "Claim")
    complaint_labels, complaint_n = combo_counter(window_rows, "Complaint")
    global_labels, global_n = combo_counter(history_rows, None)

    null_category = sum(1 for r in window_rows if not (r.get("category") or "").strip())
    null_subcategory = sum(1 for r in window_rows if not (r.get("subcategory") or "").strip())
    leak = sum(
        1
        for r in window_rows
        if (r.get("category") or "").strip()
        and (r.get("category") or "").lower() in (r.get("description") or "").lower()
    )

    # --- Claim mix + claimed amounts ---
    claims = [r for r in window_rows if (r.get("case_type") or "") == "Claim"]
    by_month: Counter = Counter()
    by_channel: Counter = Counter()
    by_priority: Counter = Counter()
    by_status: Counter = Counter()
    by_country: Counter = Counter()
    amounts_by_sub: dict[str, list[float]] = {}
    currencies: Counter = Counter()
    for row in claims:
        by_month[(row.get("creation_date") or "")[:7]] += 1
        by_channel[(row.get("reception_channel") or "") or "unknown"] += 1
        by_priority[(row.get("priority") or "") or "unknown"] += 1
        by_status[(row.get("status") or "") or "unknown"] += 1
        by_country[(row.get("country") or row.get("transaction_country") or "") or "unknown"] += 1
        amount = to_float(row.get("claimed_amount"))
        if amount is not None:
            amounts_by_sub.setdefault((row.get("subcategory") or "") or "unknown", []).append(amount)
        if (row.get("currency") or "").strip():
            currencies[(row.get("currency") or "").strip()] += 1

    # --- intent mix (interactions) ---
    try:
        interactions = iter_patterns(INTERACTION_PATS, data_dir, w=window)
    except SystemExit:
        interactions = []
    interactions = in_window(interactions, "interaction_date", start, end, ":interactions")
    reason_counter: Counter = Counter()
    for row in interactions:
        reason_counter[str((row.get("contact_reason") or "") or "unknown")] += 1
    denom = len(interactions) or 1

    def flag_rate(column: str) -> dict:
        yes = sum(1 for r in interactions if (r.get(column) or "").strip().lower() in ("true", "1", "yes"))
        return {"count": yes, "denominator": len(interactions), "share": round(yes / denom, 4)}

    # --- thresholds (transactions) ---
    try:
        transactions = iter_patterns(TRANSACTION_PATS, data_dir, w=window)
    except SystemExit:
        transactions = []
    transactions = in_window(transactions, "transaction_date", start, end, ":transactions")
    amt_by_country: dict[str, list[float]] = {}
    fraud_by_country: dict[str, list[float]] = {}
    currency_by_country: dict[str, Counter] = {}
    for row in transactions:
        country = (row.get("transaction_country") or "") or "unknown"
        amount = to_float(row.get("amount"))
        if amount is not None:
            amt_by_country.setdefault(country, []).append(amount)
        fraud = to_float(row.get("fraud_score"))
        if fraud is not None:
            fraud_by_country.setdefault(country, []).append(fraud)
        if (row.get("currency") or "").strip():
            currency_by_country.setdefault(country, Counter())[(row.get("currency") or "").strip()] += 1

    summary = {
        "meta": {
            "script_version": SCRIPT_VERSION,
            "window": window,
            "window_start": start,
            "window_end": end,
            "held_out_cut": HELD_OUT_CUT,
            "held_out_rows": 0,
            "n_complaints_window": len(window_rows),
            "n_claims_window": len(claims),
            "n_interactions_window": len(interactions),
            "n_transactions_window": len(transactions),
        },
        "labels": {
            "claim": claim_labels,
            "claim_n": claim_n,
            "complaint": complaint_labels,
            "complaint_n": complaint_n,
            "global": global_labels,
            "global_n": global_n,
        },
        "mix": {
            "by_month": dict(sorted(by_month.items())),
            "by_country": dict(sorted(by_country.items())),
            "by_channel": dict(sorted(by_channel.items())),
            "by_priority": dict(sorted(by_priority.items())),
            "by_status": dict(sorted(by_status.items())),
        },
        "amounts": {
            sub: {"n": len(values), **percentiles(values)}
            for sub, values in sorted(amounts_by_sub.items())
        },
        "amount_currencies": dict(sorted(currencies.items())),
        "label_quality": {
            "null_category": null_category,
            "null_subcategory": null_subcategory,
            "description_contains_category": leak,
            "n": len(window_rows),
        },
        "intent_mix": {
            "contact_reason": dict(sorted(reason_counter.items())),
            "denominator": len(interactions),
            "was_escalated": flag_rate("was_escalated"),
            "was_resolved": flag_rate("was_resolved"),
            "requires_followup": flag_rate("requires_followup"),
        },
        "thresholds": {
            country: {
                "n": len(values),
                "currency": (currency_by_country.get(country) or Counter()).most_common(1)[0][0]
                if currency_by_country.get(country)
                else None,
                "amount": percentiles(values),
                "fraud_score": percentiles(fraud_by_country.get(country, [])),
            }
            for country, values in sorted(amt_by_country.items())
        },
    }
    record("run", "n", len(window_rows))
    return summary


def run_folder(run_id: str) -> str:
    return os.path.join(BASE, run_id)


def manifest_hashes(data_dir: str, window: str) -> list[dict]:
    year, quarter = int(window[:4]), int(window[5])
    first_month = 3 * quarter - 2
    patterns = [
        f"complaints/year={year}/month={m:02d}/day=*/*.csv" for m in range(first_month, first_month + 3)
    ] + [
        f"windows/{window}/interactions/*/*.csv",
        f"windows/{window}/transactions/*/*.csv",
        SNAPSHOT_PRODUCTS,
    ]
    out = []
    for pattern in patterns:
        files = sorted(glob.glob(os.path.join(data_dir, pattern)))
        digest = hashlib.sha256()
        rows = 0
        for path in files:
            with open(path, "rb") as handle:
                digest.update(handle.read())
            with open(path, newline="", encoding="utf-8-sig") as handle:
                rows += sum(1 for _ in csv.DictReader(handle))
        out.append(
            {"pattern": f"data/{pattern}", "files": len(files), "rows": rows, "sha256_16": digest.hexdigest()[:16]}
        )
    return out


def do_run(run_id: str, window: str) -> None:
    data_dir = find_data()
    folder = run_folder(run_id)
    if os.path.exists(folder):
        raise SystemExit(f"refusing to overwrite committed run {folder}; use a new RUN_ID")
    summary = compute_summary(data_dir, window)
    guard_summary(summary)
    os.makedirs(folder)
    with open(os.path.join(folder, "summary.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True, ensure_ascii=False)
    hashes = manifest_hashes(data_dir, window)
    with open(os.path.join(folder, "MANIFEST.md"), "w", encoding="utf-8") as handle:
        handle.write(f"# Data manifest — {window} evaluation window\n\n")
        for entry in hashes:
            handle.write(
                f"- {entry['files']} files | {entry['rows']} rows | {entry['sha256_16']} | {entry['pattern']}\n"
            )
    with open(os.path.join(folder, "method.md"), "w", encoding="utf-8") as handle:
        handle.write(
            f"# Method — {run_id}\n\nWindow [{summary['meta']['window_start']}, "
            f"{summary['meta']['window_end']}) on event dates; held-out cut "
            f"{HELD_OUT_CUT}; aggregates only, no rows leave the process.\n"
        )
    with open(os.path.join(folder, "README.md"), "w", encoding="utf-8") as handle:
        handle.write(
            f"# {run_id}\n\nFrozen evaluation evidence for the runner: label universe, "
            "case mix, intent mix and reference thresholds.\n"
        )
    print(f"[run] wrote {folder}/summary.json")


def do_verify(run_id: str) -> None:
    data_dir = find_data()
    folder = run_folder(run_id)
    summary_path = os.path.join(folder, "summary.json")
    if not os.path.isfile(summary_path):
        raise SystemExit(f"no frozen run at {summary_path}")
    with open(summary_path, encoding="utf-8") as handle:
        frozen = json.load(handle)
    window = frozen.get("meta", {}).get("window", WINDOW_DEFAULT)
    fresh = compute_summary(data_dir, window)
    guard_summary(fresh)
    if fresh != frozen:
        for section in sorted(set(list(fresh) + list(frozen))):
            if fresh.get(section) != frozen.get(section):
                raise SystemExit(f"verify failed: section {section!r} differs; re-sync data or freeze a new run")
        raise SystemExit("verify failed: summary differs")
    print(f"[verify] {run_id} matches recomputation")


def latest_run() -> str:
    candidates = sorted(
        name
        for name in os.listdir(BASE)
        if os.path.isdir(os.path.join(BASE, name)) and re.fullmatch(r"\d{4}Q[1-4]-v\d+", name)
    )
    if not candidates:
        raise SystemExit("no frozen runs under evidence/evaluation/")
    return candidates[-1]


def do_derive(run_id: str | None = None) -> None:
    chosen = run_id or latest_run()
    summary_path = os.path.join(run_folder(chosen), "summary.json")
    with open(summary_path, encoding="utf-8") as handle:
        raw = handle.read()
    summary = json.loads(raw)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    out_dir = os.path.join(os.path.dirname(BASE), "sentinel-ai-core", "eval")
    os.makedirs(out_dir, exist_ok=True)
    labels = {
        "run_id": chosen,
        "summary_sha16": digest,
        "claim_labels": sorted(summary.get("labels", {}).get("claim", {}).keys()),
    }
    with open(os.path.join(out_dir, "labels.json"), "w", encoding="utf-8") as handle:
        json.dump(labels, handle, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"[derive] wrote sentinel-ai-core/eval/labels.json from {chosen}")


MODES = ("run", "verify", "derive")


def main(argv: list[str]) -> None:
    if "--help" in argv or "-h" in argv or not argv:
        print(__doc__.strip())
        print(f"\nmodes: {' | '.join(MODES)}")
        return
    mode = argv[0]
    if mode not in MODES:
        raise SystemExit(f"usage: eval_measure.py {' | '.join(MODES)} [RUN_ID] [WINDOW]")
    if mode == "run":
        run_id = argv[1] if len(argv) > 1 else RUN_ID_DEFAULT
        window = argv[2] if len(argv) > 2 else WINDOW_DEFAULT
        do_run(run_id, window)
    elif mode == "verify":
        do_verify(argv[1] if len(argv) > 1 else RUN_ID_DEFAULT)
    elif mode == "derive":
        do_derive(argv[1] if len(argv) > 1 else None)


if __name__ == "__main__":
    main(sys.argv[1:])
