#!/usr/bin/env python3
"""Problem measurements for the chosen workflow (development zone).

First run (v1). Answers the four questions that the "problem and demand"
slide needs, before any model exists:

  1. How many calls end at the first contact, for each reason for the call.
  2. How many calls arrive on a busy day, for each candidate workflow.
  3. How many agent hours each candidate workflow uses in one month.
  4. How much data is missing in the fields that these measures use.

Reads the raw CSVs of the data engine in place (gitignored, never committed):
  <RAW>/call_center_interactions/year=YYYY/month=MM/day=DD/*.csv
RAW defaults to <repo>/sentinel-data-engine/data/raw and can be overridden
with the SENTINEL_RAW_DIR environment variable (absolute path).

Window: the whole development zone, event dates in [2023-06-17, 2025-07-01).
Only partitions with process_date < 2025-07-01 are globbed (event dates are
equal to or one day later than process_date, so no development row is lost)
and every row is then filtered on its event date. Rows dated at or after the
held-out cut are excluded and counted. No held-out partition is read.

The reason-to-workflow mapping is fixed in code and in README.md, and it was
committed before the first number. Aggregates only: summary.json never holds
an identifier, a row or customer text.

Usage:
    python3 measure_problem.py reasons | demand | hours | missing
    python3 measure_problem.py summary   # all four + summary.json
    python3 measure_problem.py verify    # recompute MANIFEST hashes
    python3 measure_problem.py hashes    # print the MANIFEST rows

Requires duckdb (a dependency of sentinel-data-engine and sentinel-ai-core).
"""
import csv
import glob
import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from datetime import date, timedelta

import duckdb

SCRIPT_VERSION = "2026-10-05+problem-dev-v1"
HELD_OUT_CUT = "2025-07-01"
WIN_START = "2023-06-17"
WIN_END = HELD_OUT_CUT  # exclusive
WINDOW = "dev"
MONTH_DAYS = 30.4375
BOOTSTRAP = 2000
SEED = 20261005

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
RAW = os.environ.get(
    "SENTINEL_RAW_DIR", os.path.join(REPO, "sentinel-data-engine", "data", "raw")
)

# Development partitions only (process_date < cut).
DEV_MONTH_GLOBS = (
    ["year=2023/month=*/day=*/*.csv", "year=2024/month=*/day=*/*.csv"]
    + [f"year=2025/month={m:02d}/day=*/*.csv" for m in range(1, 7)]
)

# Fixed before the first number; the README holds the same table.
WORKFLOWS = {
    "account_or_payment_inquiry": "Account or payment inquiry",
    "card_support": "Card support",
    "transaction_dispute": "Transaction dispute",
    "credit_information": "Credit information",
    "other": "Other",
}
REASON_TO_WORKFLOW = {
    "Transaccional": "account_or_payment_inquiry",
    "Producto": "card_support",
    "Queja": "transaction_dispute",
    "Técnico": "other",
    "Comercial": "other",
    "Retención": "other",
}
FIELDS_USED = ["contact_reason", "reason_category", "was_resolved", "duration_seconds"]
# "other" is a residual bucket, not a candidate workflow; it is not ranked.
CANDIDATE_WORKFLOWS = [k for k in WORKFLOWS if k != "other"]

RESULTS = {}
_CON = None


def record(mode, key, value):
    RESULTS.setdefault(mode, {})[key] = value


def pct(a, b):
    return round(100.0 * a / b, 2) if b else None


def workflow_of(reason):
    """Map a reason for the call to a candidate workflow (unknown -> other)."""
    return REASON_TO_WORKFLOW.get((reason or "").strip(), "other")


def wilson(k, n, z=1.96):
    """Wilson score 95% range in percent. Returns [low, high] or [None, None]."""
    if not n:
        return [None, None]
    p = k / n
    d = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, center - half) * 100, 2),
            round(min(1.0, center + half) * 100, 2)]


def percentile(values, q):
    """Nearest-rank percentile of a list of numbers."""
    s = sorted(values)
    if not s:
        return None
    if q <= 0:
        return s[0]
    if q >= 100:
        return s[-1]
    idx = math.ceil(q / 100.0 * len(s)) - 1
    return s[max(0, min(idx, len(s) - 1))]


def bootstrap_ci(values, q, seed=None, n_boot=None):
    """95% range of the q-th percentile, from a bootstrap over the values."""
    if not values:
        return [None, None]
    seed = SEED if seed is None else seed
    n_boot = BOOTSTRAP if n_boot is None else n_boot
    rnd = random.Random(seed)
    n = len(values)
    estimates = []
    for _ in range(n_boot):
        sample = [values[rnd.randrange(n)] for _ in range(n)]
        estimates.append(percentile(sample, q))
    return [percentile(estimates, 2.5), percentile(estimates, 97.5)]


def days_in_window():
    d0 = date.fromisoformat(WIN_START)
    d1 = date.fromisoformat(WIN_END)
    return [d0 + timedelta(days=i) for i in range((d1 - d0).days)]


def files_for(table):
    out = []
    for g in DEV_MONTH_GLOBS:
        out.extend(sorted(glob.glob(os.path.join(RAW, table, g))))
    if not out:
        raise SystemExit(f"no {table} partitions under {RAW} -- sync raw data first")
    return out


def con():
    """One in-memory DuckDB with the development call rows."""
    global _CON
    if _CON is not None:
        return _CON
    files = files_for("call_center_interactions")
    c = duckdb.connect()
    rd = "header=true, all_varchar=true, union_by_name=true"
    c.execute(f"""
        create table calls_raw as
        select try_cast(interaction_date as timestamp) ts,
               nullif(trim(contact_reason), '') contact_reason,
               nullif(trim(reason_category), '') reason_category,
               try_cast(nullif(trim(duration_seconds), '') as double) duration_seconds,
               nullif(lower(trim(was_resolved)), '') was_resolved
        from read_csv({files!r}, {rd})
    """)
    c.execute(f"""create table calls as select * from calls_raw
        where ts >= timestamp '{WIN_START}' and ts < timestamp '{WIN_END}'""")
    _CON = c
    return c


def one(sql):
    return con().execute(sql).fetchone()


def rows(sql):
    return con().execute(sql).fetchall()


# --------------------------------------------------------------------------- 1
def reasons():
    print("== 1. first-contact resolution by reason ==")
    n_total, = one("select count(*) from calls_raw")
    n_dev, = one("select count(*) from calls")
    excluded = n_total - n_dev
    record("totals", "calls", n_dev)
    record("totals", "excluded_heldout", excluded)
    record("totals", "calls_read", n_total)
    print(f"calls read {n_total}, in window {n_dev}, excluded at/after cut {excluded}")

    out = {}
    for reason, n, resolved in rows("""
        select contact_reason, count(*),
               sum(case when was_resolved = 'true' then 1 else 0 end)
        from calls group by 1 order by 2 desc"""):
        lo, hi = wilson(resolved, n)
        out[reason] = {
            "n": n,
            "resolved": resolved,
            "share_pct": pct(resolved, n),
            "ci95_pct": [lo, hi],
            "workflow": workflow_of(reason),
        }
        print(f"  {reason:14s} {resolved:7d}/{n:7d} = {pct(resolved, n):5.2f}% "
              f"[{lo}, {hi}] -> {workflow_of(reason)}")
    RESULTS["reasons"] = out


# --------------------------------------------------------------------------- 2
def demand():
    print("== 2. calls per day by workflow ==")
    days = days_in_window()
    record("totals", "days", len(days))
    per_workflow = defaultdict(lambda: defaultdict(int))
    for d, reason, n in rows("""
            select cast(ts as date), contact_reason, count(*)
            from calls group by 1, 2"""):
        per_workflow[workflow_of(reason)][d] += n

    out = {}
    for wf, label in WORKFLOWS.items():
        series = [per_workflow[wf].get(d, 0) for d in days]
        p95 = percentile(series, 95)
        hi_day = max(series) if series else 0
        out[wf] = {
            "calls": sum(series),
            "days": len(series),
            "per_day_mean": round(sum(series) / len(series), 2) if series else None,
            "busy_day_p95": p95,
            "busy_day_p95_ci95": bootstrap_ci(series, 95),
            "highest_day": hi_day,
            "highest_day_ci95": bootstrap_ci(series, 100),
        }
        print(f"  {label:28s} mean {out[wf]['per_day_mean']:6.2f} "
              f"busy {p95} {out[wf]['busy_day_p95_ci95']} "
              f"high {hi_day} {out[wf]['highest_day_ci95']}")
    RESULTS["demand"] = out


# --------------------------------------------------------------------------- 3
def hours():
    print("== 3. agent hours per month by workflow ==")
    days = len(days_in_window())
    months = round(days / MONTH_DAYS, 2)
    record("totals", "months", months)

    agg = defaultdict(lambda: {"n": 0, "n_dur": 0, "missing_dur": 0, "dur_sum": 0.0})
    for reason, n, n_dur, missing_dur, mean_s in rows("""
            select contact_reason, count(*), count(duration_seconds),
                   sum(case when duration_seconds is null then 1 else 0 end),
                   avg(duration_seconds)
            from calls group by 1"""):
        a = agg[workflow_of(reason)]
        a["n"] += n
        a["n_dur"] += n_dur
        a["missing_dur"] += missing_dur
        if mean_s is not None:
            a["dur_sum"] += mean_s * n_dur

    out = {}
    raw_hours = {}
    for wf, label in WORKFLOWS.items():
        a = agg[wf]
        mean_min = round(a["dur_sum"] / a["n_dur"] / 60.0, 3) if a["n_dur"] else None
        calls_month = round(a["n"] / months, 2) if months else None
        hours_raw = a["n"] * (mean_min or 0.0) / 60.0 / months if months else 0.0
        raw_hours[wf] = hours_raw
        out[wf] = {
            "calls": a["n"],
            "n_with_duration": a["n_dur"],
            "missing_duration": a["missing_dur"],
            "mean_minutes": mean_min,
            "calls_per_month": calls_month,
            "hours_per_month": round(hours_raw, 2) if months else None,
            "rank": None,
        }
    ranked = sorted(CANDIDATE_WORKFLOWS,
                    key=lambda w: raw_hours[w], reverse=True)
    for i, wf in enumerate(ranked, 1):
        out[wf]["rank"] = i
    for wf in CANDIDATE_WORKFLOWS + ["other"]:
        tag = f"{out[wf]['rank']}." if out[wf]["rank"] else " -"
        print(f"  {tag} {WORKFLOWS[wf]:28s} "
              f"{out[wf]['hours_per_month']:8.2f} h/month "
              f"({out[wf]['calls']} calls, {out[wf]['mean_minutes']} min)")
    RESULTS["hours"] = out


# --------------------------------------------------------------------------- 4
def missing():
    print("== 4. missing values in the fields used ==")
    n, = one("select count(*) from calls")
    out = {}
    for col in FIELDS_USED:
        miss, = one(f"select sum(case when {col} is null then 1 else 0 end) from calls")
        miss = miss or 0
        lo, hi = wilson(miss, n)
        out[col] = {
            "n": n,
            "missing": miss,
            "share_pct": pct(miss, n),
            "ci95_pct": [lo, hi],
        }
        print(f"  {col:18s} {miss:7d}/{n} = {pct(miss, n)}% [{lo}, {hi}]")
    RESULTS["missing"] = out


def build_summary():
    return {
        "script_version": SCRIPT_VERSION,
        "kind": "problem_evidence",
        "window": WINDOW,
        "window_start": WIN_START,
        "window_end": WIN_END,
        "held_out_cut": HELD_OUT_CUT,
        "source": {
            "table": "call_center_interactions",
            "origin": "measured",
            "field": "contact_reason",
        },
        "mapping": REASON_TO_WORKFLOW,
        "workflow_labels": WORKFLOWS,
        "totals": RESULTS.get("totals", {}),
        "reasons": RESULTS.get("reasons", {}),
        "demand": RESULTS.get("demand", {}),
        "hours": RESULTS.get("hours", {}),
        "missing": RESULTS.get("missing", {}),
        "notes": [
            "The dataset is synthetic. The numbers describe the dataset, not a real bank.",
            "First contact means the dataset field was_resolved; the dataset does not tell if the customer called again.",
            "The busy-day level is the 95th percentile of the daily counts; the range comes from a bootstrap over the days.",
            "Mean handling time uses only the calls with a duration; the calls without one are counted, not filled.",
            "The mapping is a judgment; a different mapping can change the ranking.",
            "The product field is empty on most transactional calls, so the mapping uses the reason only.",
            "Aggregates only: no row, identifier or text is written.",
        ],
    }


def summary():
    for f in (reasons, demand, hours, missing):
        f()
    out = build_summary()
    with open(os.path.join(BASE, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("[summary] wrote summary.json")


def compute_summary(raw_dir=None):
    """Reset, run all four modes on raw_dir, and return the summary dict."""
    global RAW, _CON, RESULTS
    if raw_dir is not None:
        RAW = raw_dir
    _CON = None
    RESULTS = {}
    reasons()
    demand()
    hours()
    missing()
    return build_summary()


# ---------------------------------------------------------------------- verify
def hash_groups():
    groups = []
    for table in ("call_center_interactions",):
        for g in DEV_MONTH_GLOBS:
            fs = sorted(glob.glob(os.path.join(RAW, table, g)))
            if fs:
                groups.append((f"{table}/{g}", fs))
    out = []
    for name, fs in groups:
        h = hashlib.sha256()
        nrows = 0
        for f in fs:
            with open(f, "rb") as fh:
                h.update(fh.read())
            with open(f, newline="", encoding="utf-8-sig") as fh:
                nrows += sum(1 for _ in csv.DictReader(fh))
        out.append((name, len(fs), nrows, h.hexdigest()[:16]))
    return out


def verify():
    manifest = open(os.path.join(BASE, "MANIFEST.md"), encoding="utf-8").read()
    ok = True
    for name, nf, nr, hx in hash_groups():
        line = f"| {nf} | {nr:,} | {hx} | {name} |"
        hit = line in manifest
        ok &= hit
        print(("OK   " if hit else "DIFF ") + line)
    raise SystemExit(0 if ok else 1)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "summary"
    if mode == "verify":
        verify()
    if mode == "hashes":
        for name, nf, nr, hx in hash_groups():
            print(f"| {nf} | {nr:,} | {hx} | {name} |")
        return
    if mode == "summary":
        summary()
        return
    if mode not in MODES:
        raise SystemExit(__doc__)
    MODES[mode]()


MODES = {"reasons": reasons, "demand": demand, "hours": hours, "missing": missing}


if __name__ == "__main__":
    main()
