#!/usr/bin/env python3
"""Reusable flow measurements for the Tuesday 9/29 flow review.

Self-contained: data/ (gitignored) and summary.json live next to this script.

Reads raw CSVs from ./data/ (never edit data by hand).
Layout: data/complaints/year=YYYY/month=MM/ (full history on disk),
data/snapshots/*.csv, data/windows/<WINDOW>/{interactions,transactions,transcripts}/.
Stdlib only -- no pandas needed.

Partitions are by process_date, but ~25% of rows carry
an event date 1 day later (synthetic offset). The analysis window is therefore
defined on EVENT dates (creation_date / interaction_date / transaction_date),
never on partitions. Rows outside the window are excluded and reported.

Cleaning (applied to every row before counting):
  1. utf-8-sig decoding (strips BOM in older headers),
  2. strip whitespace on all values (blank == missing),
  3. drop fully-empty rows (reported, never silent).

Usage:
    python3 measure_flow.py disputes | accounts | cards | credit [WINDOW]
    python3 measure_flow.py summary [WINDOW]   # all four + summary.json
    python3 measure_flow.py verify             # recompute MANIFEST hashes
    WINDOW like 2024Q4 (dev zone). Held-out cut 2025-07-01 (70/30 split):
    development = 2023-06 -> 2025-06, held-out = 2025-07 -> 2026-06.
    Data at/after the cut must not be downloaded before the single final
    held-out measurement.
"""
import csv
import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

SCRIPT_VERSION = "2026-09-28+q4-7030"
RESULTS = {}

# Held-out cut (70/30 time split): development < 2025-07-01, held-out >= it.
HELD_OUT_CUT = "2025-07-01"

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")


def record(mode, key, value):
    """Store a machine-readable metric for the summary mode."""
    RESULTS.setdefault(mode, {})[key] = value
WINDOW = sys.argv[2] if len(sys.argv) > 2 else "2024Q4"
WIN = os.path.join(DATA, "windows", WINDOW)

M = re.fullmatch(r"(\d{4})Q([1-4])", WINDOW)
if not M:
    raise SystemExit(f"WINDOW must look like 2024Q4, got {WINDOW!r}")
WYEAR, WQ = int(M.group(1)), int(M.group(2))
FIRST_MONTH = 3 * WQ - 2
WIN_START = f"{WYEAR}-{FIRST_MONTH:02d}-01"
_END_M = FIRST_MONTH + 3
_END_Y = WYEAR + (1 if _END_M > 12 else 0)
_END_M = _END_M - 12 if _END_M > 12 else _END_M
WIN_END = f"{_END_Y}-{_END_M:02d}-01"  # exclusive
COMPLAINT_PATS = [
    f"complaints/year={WYEAR}/month={m:02d}/day=*/*.csv"
    for m in range(FIRST_MONTH, FIRST_MONTH + 3)
]


def scan(pattern, encoding="utf-8-sig"):
    """Yield cleaned rows from all CSVs matching a glob under data/."""
    files = sorted(glob.glob(os.path.join(DATA, pattern)))
    if not files:
        raise SystemExit(f"no files match data/{pattern} -- sync from S3 first")
    n_files = 0
    dropped = 0
    for f in files:
        with open(f, newline="", encoding=encoding) as fh:
            for row in csv.DictReader(fh):
                clean = {k: (v.strip() if isinstance(v, str) else v)
                         for k, v in row.items()}
                if not any(clean.values()):
                    dropped += 1
                    continue
                yield clean
        n_files += 1
    print(f"[scan] {n_files} files under data/{pattern} "
          f"(dropped {dropped} fully-empty rows)")


def value_counts(rows, *cols, limit=15):
    """Count distinct value combos of cols over an iterable of rows."""
    c = Counter()
    n = 0
    for row in rows:
        n += 1
        c[tuple((row.get(col) or "").strip() for col in cols)] += 1
    if n == 0:
        print("[counts] n=0 (empty input -- check filters)")
        return 0, c
    print(f"[counts] n={n} distinct={len(c)}")
    for k, v in c.most_common(limit):
        print(f"  {v:7d} ({v / n * 100:5.2f}%)  {k}")
    if len(c) > limit:
        rest = sum(v for _, v in c.most_common()[limit:])
        print(f"  ... {len(c) - limit} more combos omitted ({rest} rows, "
              f"{rest / n * 100:.2f}%) -- sums in docs must use the full counter")
    return n, c


def in_window(rows, event_col, label=""):
    """Keep rows whose event date falls inside [WIN_START, WIN_END)."""
    kept, out = [], 0
    for row in rows:
        d = (row.get(event_col) or "")[:10]
        if WIN_START <= d < WIN_END:
            kept.append(row)
        else:
            out += 1
    print(f"[window{label}] event {event_col} in [{WIN_START}, {WIN_END}): "
          f"kept {len(kept)}, excluded {out}")
    return kept


def quality_id(rows, id_col, label=""):
    """Duplicate check on an id column. Returns (n, n_unique, n_extra)."""
    ids = Counter()
    n = 0
    for row in rows:
        n += 1
        ids[(row.get(id_col) or "").strip()] += 1
    dups = sum(1 for v in ids.values() if v > 1)
    extra = sum(v - 1 for v in ids.values() if v > 1)
    pct = extra / n * 100 if n else 0.0
    print(f"[quality{label}] n={n} unique={len(ids)} dup_ids={dups} "
          f"extra_rows={extra} ({pct:.2f}%)")
    return n, len(ids), extra


def nulls(rows, cols):
    """Count blank values per column."""
    c = Counter()
    n = 0
    for row in rows:
        n += 1
        for col in cols:
            if not (row.get(col) or "").strip():
                c[col] += 1
    print(f"[nulls] n={n} " + str(dict(c)))
    return dict(c)


def date_guard(rows, date_cols, label=""):
    """Fail loudly if any row reaches the held-out zone (>= HELD_OUT_CUT)."""
    bad = 0
    n = 0
    for row in rows:
        n += 1
        for col in date_cols:
            v = (row.get(col) or "").strip()[:10]
            if v >= HELD_OUT_CUT:
                bad += 1
                break
    print(f"[date-guard{label}] n={n} rows at/after {HELD_OUT_CUT}: {bad}")
    return bad


def snapshot_filtered(path, date_col="last_updated", cutoff=HELD_OUT_CUT):
    """Load a snapshot keeping rows updated strictly before cutoff."""
    rows, excluded = [], 0
    for row in scan(path):
        if (row.get(date_col) or "").strip() >= cutoff:
            excluded += 1
            continue
        rows.append(row)
    print(f"[snapshot-filter] {path}: kept {len(rows)}, excluded {excluded} "
          f"({date_col} >= {cutoff[:10]})")
    return rows


def disputes():
    print(f"=== disputes: window {WINDOW} (event dates) ===")
    raw = []
    for p in COMPLAINT_PATS:
        raw.extend(scan(p))
    rows = in_window(raw, "creation_date", ":complaints")
    n, n_unique, extra = quality_id(iter(rows), "complaint_id", ":complaints")
    record("disputes", "n", n)
    record("disputes", "dup_extra_rows", extra)
    nulls(iter(rows), ["case_type", "category", "subcategory", "origin_interaction_id"])
    bad = date_guard(iter(rows), ["creation_date", "process_date"], ":complaints")
    record("disputes", "rows_in_heldout", bad)
    print("-- case_type --")
    _, cc = value_counts(iter(rows), "case_type")
    record("disputes", "claims", sum(v for k, v in cc.items() if k == ("Claim",)))
    print("-- category within Claim --")
    claim = [r for r in rows if (r.get("case_type") or "") == "Claim"]
    value_counts(iter(claim), "category", "subcategory")
    print("-- 'Cargo no reconocido' across case_types --")
    cnr = [r for r in rows if (r.get("subcategory") or "").strip() == "Cargo no reconocido"]
    _, cnrc = value_counts(iter(cnr), "case_type")
    record("disputes", "unrecognized_claim",
           sum(v for k, v in cnrc.items() if k == ("Claim",)))
    record("disputes", "unrecognized_complaint",
           sum(v for k, v in cnrc.items() if k == ("Complaint",)))
    print("-- origin_interaction_id fill --")
    filled = sum(1 for r in rows if (r.get("origin_interaction_id") or "").strip())
    denom = len(rows) or 1
    print(f"[linkage] {filled}/{len(rows)} filled ({filled / denom * 100:.2f}%)")
    record("disputes", "linkage_filled", filled)
    print("-- description leak check (non-empty category only) --")
    leak = sum(1 for r in rows
               if (r.get("category") or "").strip()
               and (r.get("category") or "").lower() in (r.get("description") or "").lower())
    print(f"[leak] description contains category: {leak}/{len(rows)} ({leak / len(rows) * 100:.1f}%)")
    record("disputes", "description_leak", leak)
    print("-- transcript join + text signal (full window) --")
    inter = {}
    for r in scan(f"windows/{WINDOW}/interactions/*/*.csv"):
        iid = (r.get("interaction_id") or "").strip()
        if iid:
            inter[iid] = (r.get("contact_reason", ""), r.get("reason_category", ""))
    trows = []
    for r in scan(f"windows/{WINDOW}/transcripts/*/*/*.csv"):
        trows.append(r)
    print(f"[scan] {len(trows)} transcripts collected (full window, no truncation)")
    hit = sum(1 for t in trows if (t.get("interaction_id") or "").strip() in inter)
    ct = Counter((t.get("customer_text") or "")[:60] for t in trows)
    denom = len(trows) or 1
    print(f"[join] {hit}/{len(trows)} transcripts match a call "
          f"({hit / denom * 100:.1f}%)")
    print(f"[text] {len(trows)} transcripts, {len(ct)} distinct prefixes")
    for k, v in ct.most_common(5):
        print(f"  {v:5d}  {k!r}")
    record("disputes", "transcripts", len(trows))
    record("disputes", "join_hit", hit)
    record("disputes", "text_prefixes", len(ct))


def accounts():
    print(f"=== accounts: window {WINDOW} (event dates) ===")
    raw = list(scan(f"windows/{WINDOW}/transactions/*/*.csv"))
    rows = in_window(raw, "transaction_date", ":transactions")
    quality_id(iter(rows), "transaction_id", ":transactions")
    nulls(iter(rows), ["transaction_status", "channel", "is_fraud"])
    date_guard(iter(rows), ["transaction_date", "process_date"], ":transactions")
    _, sc = value_counts(iter(rows), "transaction_status")
    record("accounts", "n_transactions", len(rows))
    for status in ("Approved", "Declined", "Pending", "Reversed"):
        record("accounts", f"status_{status}",
               sum(v for k, v in sc.items() if k == (status,)))
    print("-- channel mix --")
    value_counts(iter(rows), "channel")
    print("-- fraud flags in sample --")
    _, fc = value_counts(iter(rows), "is_fraud")
    record("accounts", "fraud_true", sum(v for k, v in fc.items() if k == ("True",)))
    print("-- call reasons (window) --")
    iraw = list(scan(f"windows/{WINDOW}/interactions/*/*.csv"))
    irows = in_window(iraw, "interaction_date", ":interactions")
    _, rc = value_counts(iter(irows), "contact_reason")
    record("accounts", "n_calls", len(irows))
    record("accounts", "reason_transaccional",
           sum(v for k, v in rc.items() if k == ("Transaccional",)))


def cards():
    print(f"=== cards: window {WINDOW} (event dates) ===")
    prods = snapshot_filtered("snapshots/products.csv")
    quality_id(iter(prods), "product_id", ":products")
    nulls(iter(prods), ["product_type", "product_status"])
    date_guard(iter(prods), ["last_updated"], ":products")
    print("-- product_type x product_status --")
    value_counts(iter(prods), "product_type", "product_status")
    print("-- declines + fraud in window transactions --")
    raw = list(scan(f"windows/{WINDOW}/transactions/*/*.csv"))
    rows = in_window(raw, "transaction_date", ":transactions")
    dec = [r for r in rows if (r.get("transaction_status") or "") in ("Declined", "Pending", "Reversed")]
    print(f"[declines] {len(dec)}/{len(rows)} ({len(dec) / len(rows) * 100:.2f}%)")
    record("cards", "actionable", len(dec))
    _, fc = value_counts(iter(rows), "is_fraud")
    record("cards", "fraud_true", sum(v for k, v in fc.items() if k == ("True",)))
    tc = Counter((r.get("product_type") or "").strip() for r in prods)
    record("cards", "credit_cards",
           sum(v for k, v in tc.items() if k == "Tarjeta Crédito"))
    record("cards", "blocked",
           sum(1 for r in prods if (r.get("product_status") or "").strip() == "Blocked"))


def credit():
    print("=== credit: portfolio + delinquency ===")
    prods = snapshot_filtered("snapshots/products.csv")
    print("-- loan/credit products --")
    value_counts(iter(prods), "product_type", "product_status")
    print("-- days_past_due buckets (products) --")
    def bucket(r):
        try:
            d = float(r.get("days_past_due") or 0)
        except ValueError:
            return "null"
        if d <= 0:
            return "current"
        if d <= 30:
            return "1-30"
        if d <= 90:
            return "31-90"
        return ">90"
    b = Counter(bucket(r) for r in prods)
    n = len(prods)
    for k, v in b.most_common():
        print(f"  {v:7d} ({v / n * 100:5.2f}%)  {k}")
    record("credit", "n_products", n)
    record("credit", "delinquent", sum(v for k, v in b.items() if k != "current"))


def ci95(k, n):
    """Normal-approx 95% CI half-width in percentage points."""
    if n == 0:
        return 0.0
    import math
    p = k / n
    return 1.96 * math.sqrt(p * (1 - p) / n) * 100


def summary():
    """Run all four modes, then write summary.json (the deterministic record)."""
    for mode in ("disputes", "accounts", "cards", "credit"):
        MODES[mode]()
    d = RESULTS["disputes"]
    out = {
        "script_version": SCRIPT_VERSION,
        "window": WINDOW,
        "window_start": WIN_START,
        "window_end": WIN_END,
        "disputes": {**d,
                      "dispute_share_pct": round(d["unrecognized_claim"] / d["n"] * 100, 2),
                      "dispute_share_ci95pp": round(ci95(d["unrecognized_claim"], d["n"]), 2)},
        "accounts": RESULTS["accounts"],
        "cards": RESULTS["cards"],
        "credit": RESULTS["credit"],
    }
    with open("summary.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print("[summary] wrote summary.json "
          f"(script {SCRIPT_VERSION}, window {WINDOW})")


# verify() always checks the 2024Q4 reference window (detects data drift).
MANIFEST_PATTERNS = [
    "complaints/year=2024/month=10/day=*/*.csv",
    "complaints/year=2024/month=11/day=*/*.csv",
    "complaints/year=2024/month=12/day=*/*.csv",
    "windows/2024Q4/interactions/day=*/*.csv",
    "windows/2024Q4/transactions/day=*/*.csv",
    "windows/2024Q4/transcripts/*/*/*.csv",
    "snapshots/products.csv",
]


def verify():
    """Recompute sha256 + row counts; compare visually against MANIFEST.md."""
    for pat in MANIFEST_PATTERNS:
        fs = sorted(glob.glob(os.path.join(DATA, pat)))
        n = 0
        h = hashlib.sha256()
        for f in fs:
            with open(f, "rb") as fh:
                h.update(fh.read())
            with open(f, newline="", encoding="utf-8-sig") as fh:
                n += sum(1 for _ in csv.DictReader(fh))
        print(f"{len(fs):4d} files | {n:7d} rows | {h.hexdigest()[:16]} | {pat}")
    print("[verify] compare each line against MANIFEST.md -- any mismatch: "
          "re-sync from S3 and re-run everything")


MODES = {"disputes": disputes, "accounts": accounts, "cards": cards,
         "credit": credit, "summary": summary, "verify": verify}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in MODES:
        sys.exit(f"usage: {sys.argv[0]} {' | '.join(MODES)} [WINDOW]")
    MODES[sys.argv[1]]()
