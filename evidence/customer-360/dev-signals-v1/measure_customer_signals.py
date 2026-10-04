#!/usr/bin/env python3
"""Customer transaction-signal measurements ("unusual for this customer").

Second Customer 360 run (dev-signals-v1). The first run
(evidence/customer-360/dev-v1) found no usable signal in product status,
pre-authorization pairs, duplicates or complaint history. This run asks
whether deterministic, charge-time, customer-relative transaction signals
(amount vs own history, first-time merchant / category / country / channel /
hour bucket, distance from usual location, bursts) carry information about
`is_fraud`, and whether they add anything beyond `fraud_score` and the p95
handoff rule of decision 010.

Reads the raw CSVs of the data engine (gitignored, never committed):
  <RAW>/customers.csv                                (customer_id, country only)
  <RAW>/transactions/year=YYYY/month=MM/day=DD/*.csv (process_date partitions)
RAW defaults to <repo>/sentinel-data-engine/data/raw and can be overridden
with the SENTINEL_RAW_DIR environment variable (absolute path).

Window: development zone, event dates in [2023-06-01, 2025-07-01). Only
partitions with process_date < 2025-07-01 are globbed. Temporal split inside
the window: FIT = [2023-06-01, 2025-01-01) (thresholds, percentiles, model
weights), REPORT = [2025-01-01, 2025-07-01) (every headline number).

Leakage rules: customer-history features use only transactions strictly
before the scored one (ordered by transaction_date, then transaction_id as a
deterministic tie-break); `is_fraud` is the label only, never a feature. All
customers are used (no sampling). Only aggregates leave this script:
summary.json never holds identifiers, rows, merchant names or amounts of
individual records.

Usage:
    python3 measure_customer_signals.py labels | signals | incremental
    python3 measure_customer_signals.py summary   # all three + summary.json
    python3 measure_customer_signals.py verify    # recompute MANIFEST hashes
    python3 measure_customer_signals.py hashes    # print MANIFEST hash lines
"""
import csv
import glob
import hashlib
import json
import math
import os
import sys

import duckdb
import numpy as np

# Rows are fetched in (transaction_date, transaction_id) order so the seeded
# bootstrap resamples the same rows on every run.

SCRIPT_VERSION = "2026-10-04+c360-dev-signals-v1"
HELD_OUT_CUT = "2025-07-01"
WINDOW = "dev"
WIN_START = "2023-06-01"
WIN_END = HELD_OUT_CUT  # exclusive
SPLIT = "2025-01-01"    # FIT < SPLIT <= REPORT

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
RAW = os.environ.get(
    "SENTINEL_RAW_DIR", os.path.join(REPO, "sentinel-data-engine", "data", "raw")
)

DEV_MONTH_GLOBS = (
    ["year=2023/month=*/day=*/*.csv", "year=2024/month=*/day=*/*.csv"]
    + [f"year=2025/month={m:02d}/day=*/*.csv" for m in range(1, 7)]
)

# Canonical country spelling (as in evidence/evaluation/eval_measure.py).
COUNTRY_CANON = {"Mexico": "México"}

# Fixed parameters (copied into summary.json).
MIN_HISTORY = 5          # prior transactions needed before a customer-relative signal is defined
MIN_GROUP = 100          # decision 010: a (country, currency) group needs >= 100 charges
RULE_PERCENTILE = 0.95   # decision 010: p95 of fraud_score
SIGNAL_PERCENTILE = 0.95 # amount / distance cut-offs are the FIT-part p95
BURST_SHORT_MIN = 10     # burst: >= 1 other transaction of the customer in the prior 10 minutes
BURST_LONG_MIN = 60      # burst: >= BURST_LONG_N others in the prior 60 minutes
BURST_LONG_N = 2
HOUR_BUCKET_H = 4        # 6 buckets of 4 hours
N_BOOT = 200             # paired bootstrap resamples for AUC deltas
SEED = 20261004
Z95 = 1.959964

# Flag rule (fixed in code, copied into summary.json).
SPARSE_DEFINED_PCT = 20.0  # signal computable on < 20% of REPORT rows -> undefined_too_sparse
SPARSE_EXPECTED_FRAUD = 5  # or signal-on REPORT rows x base rate < 5 expected frauds (no power)
USEFUL_LIFT_LOW = 1.5      # useful: Wilson-low lift >= 1.5 AND bootstrap-low delta AUC > 0
FLAG_RULE = (
    f"undefined_too_sparse if report defined_pct < {SPARSE_DEFINED_PCT} or the signal-on report "
    f"rows hold < {SPARSE_EXPECTED_FRAUD} expected frauds at the base rate; "
    f"useful if report lift_ci_low >= {USEFUL_LIFT_LOW} and incremental delta_auc_ci_low > 0; "
    "weak if report lift_ci_low > 1.0 or incremental delta_auc_ci_low > 0 (but not useful); "
    "none otherwise. investigation.has_signal = any signal flagged useful."
)

RESULTS = {}


def record(mode, key, value):
    RESULTS.setdefault(mode, {})[key] = value


def pct(a, b):
    return round(100.0 * a / b, 3) if b else None


def wilson(k, n):
    if not n:
        return (None, None)
    p = k / n
    d = 1 + Z95 ** 2 / n
    c = (p + Z95 ** 2 / (2 * n)) / d
    h = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def rate_block(k, n, base=None):
    """Rate with Wilson 95% interval; lift vs a fixed base rate."""
    lo, hi = wilson(k, n)
    out = {"n": n, "fraud": k, "rate_pct": pct(k, n),
           "rate_ci_pct": [round(100 * lo, 3), round(100 * hi, 3)] if n else None}
    if base:
        out["lift"] = round((k / n) / base, 3) if n else None
        out["lift_ci"] = [round(lo / base, 3), round(hi / base, 3)] if n else None
    return out


def files_for(table):
    out = []
    for g in DEV_MONTH_GLOBS:
        out.extend(sorted(glob.glob(os.path.join(RAW, table, g))))
    if not out:
        raise SystemExit(f"no {table} partitions under {RAW} -- sync raw data first")
    return out


_CON = None


def con():
    """In-memory DuckDB: dev transactions with customer-relative features."""
    global _CON
    if _CON is not None:
        return _CON
    if not os.path.exists(os.path.join(RAW, "customers.csv")):
        raise SystemExit(f"missing customers.csv under {RAW}")
    c = duckdb.connect()
    rd = "header=true, all_varchar=true"
    canon = " ".join(f"when '{k}' then '{v}'" for k, v in COUNTRY_CANON.items())
    c.execute(f"""
        create table cu as
        select trim(customer_id) customer_id,
               case trim(country) {canon} else trim(country) end country,
               trim(country) country_raw
        from read_csv('{os.path.join(RAW, "customers.csv")}', {rd})""")
    c.execute(f"""
        create table t_raw as
        select trim(transaction_id) transaction_id,
               try_cast(transaction_date as timestamp) ts,
               trim(customer_id) customer_id,
               trim(transaction_type) transaction_type,
               try_cast(amount as double) amount, trim(currency) currency,
               try_cast(nullif(trim(amount_usd), '') as double) amount_usd,
               trim(channel) channel,
               nullif(trim(merchant_name), '') merchant_name,
               nullif(trim(merchant_category), '') merchant_category,
               trim(transaction_country) country_raw,
               case trim(transaction_country) {canon} else trim(transaction_country) end txn_country,
               trim(transaction_status) status,
               lower(trim(is_fraud)) = 'true' is_fraud,
               try_cast(nullif(trim(fraud_score), '') as double) fraud_score,
               try_cast(nullif(trim(latitude), '') as double) lat,
               try_cast(nullif(trim(longitude), '') as double) lon
        from read_csv({files_for("transactions")!r}, {rd}, union_by_name=true)""")
    c.execute(f"""create table t as select t_raw.*, cu.country acct_country,
               case when ts < timestamp '{SPLIT}' then 'fit' else 'report' end part
        from t_raw left join cu using (customer_id)
        where ts >= timestamp '{WIN_START}' and ts < timestamp '{WIN_END}'""")
    _CON = c
    return c


def one(sql):
    return con().execute(sql).fetchone()


def rows(sql):
    return con().execute(sql).fetchall()


def fnum(v):
    """DuckDB numpy column (possibly masked) -> float array with NaN for NULL."""
    return np.ma.asarray(v).astype(float).filled(np.nan)


def auc(y, s):
    """Mann-Whitney AUC with average ranks for ties."""
    y = np.asarray(y, bool)
    s = np.asarray(s, float)
    n1 = int(y.sum())
    n0 = len(y) - n1
    if not n1 or not n0:
        return None
    order = np.argsort(s, kind="mergesort")
    ss = s[order]
    ranks = np.empty(len(s), float)
    # average ranks over tie blocks
    bounds = np.flatnonzero(np.diff(ss)) + 1
    starts = np.concatenate(([0], bounds))
    ends = np.concatenate((bounds, [len(ss)]))
    avg = (starts + ends + 1) / 2.0
    ranks[order] = np.repeat(avg, ends - starts)
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


# --------------------------------------------------------------------- labels
def labels():
    print("== 1. label sanity ==")
    n, nf = one("select count(*), sum(is_fraud::int) from t")
    record("labels", "n_dev", n)
    record("labels", "fraud_dev", nf)
    record("labels", "prevalence_pct", pct(nf, n))
    for part in ("fit", "report"):
        k, m = one(f"select sum(is_fraud::int), count(*) from t where part = '{part}'")
        record("labels", f"prevalence_{part}", rate_block(k, m))
    print(f"rows {n}, fraud {nf} ({pct(nf, n)}%)")

    base = nf / n
    dims = {
        "transaction_country_normalized": "txn_country",
        "account_country": "coalesce(acct_country, '(no customer)')",
        "currency": "currency", "channel": "channel",
        "transaction_type": "transaction_type", "transaction_status": "status",
        "fraud_score_missing": "(fraud_score is null)::varchar",
        "merchant_name_present": "(merchant_name is not null)::varchar",
        "lat_long_present": "(lat is not null)::varchar",
        "hour_of_day": "lpad(hour(ts)::varchar, 2, '0')",
    }
    by = {}
    excl = {}
    for name, expr in dims.items():
        d = {}
        n_excl = 0
        for v, m, k in rows(f"select {expr}, count(*), sum(is_fraud::int) from t group by 1 order by 1"):
            b = rate_block(k, m, base)
            d[str(v)] = b
            if b["lift_ci"][0] > 1 or b["lift_ci"][1] < 1:
                n_excl += 1
        by[name] = d
        excl[name] = {"levels": len(d), "levels_ci_excluding_base": n_excl}
    record("labels", "by", by)
    record("labels", "levels_with_lift_ci_excluding_1", excl)

    # Country spelling normalisation.
    record("labels", "country_normalization", {
        "rule": COUNTRY_CANON,
        "transaction_rows_normalized": one(
            "select count(*) from t where country_raw <> txn_country")[0],
        "customer_rows_normalized": one(
            "select count(*) from cu where country_raw <> country")[0],
        "transaction_country_raw_levels": [r[0] for r in rows(
            "select distinct country_raw from t order by 1")],
        "customer_country_levels": [r[0] for r in rows(
            "select distinct country from cu order by 1")],
    })

    # Customer clustering of fraud vs independence (Poisson expectation).
    obs = {int(k): v for k, v in rows("""
        select nf, count(*) from (select customer_id, sum(is_fraud::int) nf
        from t group by 1) group by 1 order by 1""")}
    ncust = sum(obs.values())
    lam = nf / ncust
    exp = {k: round(ncust * math.exp(-lam) * lam ** k / math.factorial(k), 1) for k in obs}
    record("labels", "fraud_per_customer", {"customers": ncust, "observed": obs,
                                            "poisson_expected": exp})

    # fraud_score distribution.
    dist = {}
    for f, cnt, nn, mn, mx, q in rows("""
        select is_fraud, count(*), count(fraud_score), min(fraud_score), max(fraud_score),
               quantile_cont(fraud_score, [0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
        from t group by 1"""):
        dist["fraud" if f else "non_fraud"] = {
            "n": cnt, "score_missing_pct": pct(cnt - nn, cnt), "min": mn, "max": mx,
            "p05_p25_p50_p75_p95_p99": [round(x, 2) for x in q]}
    record("labels", "fraud_score_distribution", dist)
    bound = dist["non_fraud"]["max"]
    above_f, above_n, scored_f = one(f"""select sum((is_fraud and fraud_score > {bound})::int),
        sum((not is_fraud and fraud_score > {bound})::int),
        sum((is_fraud and fraud_score is not null)::int) from t""")
    record("labels", "synthetic_artefact", {
        "non_fraud_score_max": bound,
        "fraud_with_score_above_non_fraud_max": above_f,
        "fraud_with_score_above_non_fraud_max_pct_of_scored_fraud": pct(above_f, scored_f),
        "non_fraud_with_score_above_non_fraud_max": above_n,
        "score_above_bound_precision_pct": pct(above_f, above_f + above_n),
        "reading": ("fraud_score of non-fraud rows never exceeds the bound; any score above it "
                    "is fraud with certainty. Below it fraud and non-fraud overlap. is_fraud "
                    "itself is not a deterministic function of one field."),
    })

    # AUC of fraud_score alone, per part (scored rows only, and missing ranked lowest).
    aucs = {}
    for part in ("fit", "report"):
        y, s = con().execute(f"select is_fraud, fraud_score from t where part = '{part}' order by ts, transaction_id").fetchnumpy().values()
        y = fnum(y).astype(bool)
        s = fnum(s)
        m = ~np.isnan(s)
        aucs[part] = {"scored_rows": round(auc(y[m], s[m]), 4),
                      "all_rows_missing_as_lowest": round(auc(y, np.where(m, s, -1.0)), 4),
                      "scored_rows_n": int(m.sum()), "scored_fraud": int(y[m].sum())}
    record("labels", "fraud_score_auc", aucs)
    print("fraud_score AUC:", aucs)

    # Decision 010 p95 rule, re-derived on FIT, applied on REPORT (strict >).
    thr = rows(f"""
        select coalesce(acct_country, '(no customer)'), currency, count(fraud_score),
               quantile_cont(fraud_score, {RULE_PERCENTILE})
        from t where part = 'fit' group by 1, 2 order by 1, 2""")
    con().execute("create or replace table thr (c varchar, cur varchar, n bigint, p double)")
    con().executemany("insert into thr values (?, ?, ?, ?)", thr)
    tp, fp, fn_scored, fn_unscored, fired_n = one(f"""
        with r as (select t.is_fraud, (t.fraud_score > thr.p) fire
                   from t left join thr on coalesce(t.acct_country, '(no customer)') = thr.c
                                       and t.currency = thr.cur and thr.n >= {MIN_GROUP}
                   where part = 'report')
        select sum((is_fraud and coalesce(fire, false))::int),
               sum((not is_fraud and coalesce(fire, false))::int),
               sum((is_fraud and fire = false)::int),
               sum((is_fraud and fire is null)::int),
               sum(coalesce(fire, false)::int) from r""")
    nrep, = one("select count(*) from t where part = 'report'")
    record("labels", "p95_rule", {
        "derivation": ("decision 010: p95 (linear interpolation) of fraud_score per account "
                       "country (customers.country, 'Mexico' -> 'México') and charge currency, "
                       f"groups >= {MIN_GROUP} scored charges, all statuses and types; fitted on FIT, "
                       "fires when fraud_score > threshold (strict, as in app/policy/engine.py); "
                       "evaluated on REPORT"),
        "thresholds_fit": {f"{c}|{cur}": {"n": nn, "p95": round(p, 2) if nn >= MIN_GROUP else None}
                           for c, cur, nn, p in thr},
        "report_fired_pct": pct(fired_n, nrep),
        "true_positive": tp, "false_positive": fp,
        "fraud_missed_scored": fn_scored, "fraud_missed_no_score_or_no_threshold": fn_unscored,
        "precision_pct": pct(tp, tp + fp),
        "precision_ci_pct": [round(100 * x, 3) for x in wilson(tp, tp + fp)],
        "recall_pct": pct(tp, tp + fn_scored + fn_unscored),
        "recall_ci_pct": [round(100 * x, 3) for x in wilson(tp, tp + fn_scored + fn_unscored)],
        "recall_among_scored_fraud_pct": pct(tp, tp + fn_scored),
    })
    bfit, = one("select max(fraud_score) from t where part = 'fit' and not is_fraud")
    btp, bfp, bf = one(f"""select sum((is_fraud and fraud_score > {bfit})::int),
        sum((not is_fraud and fraud_score > {bfit})::int), sum(is_fraud::int)
        from t where part = 'report'""")
    record("labels", "bound_rule", {
        "derivation": "fires when fraud_score > the FIT-part maximum score of non-fraud rows; evaluated on REPORT",
        "threshold_fit": bfit, "true_positive": btp, "false_positive": bfp,
        "precision_pct": pct(btp, btp + bfp), "recall_pct": pct(btp, bf),
        "report_fired_pct": pct(btp + bfp, nrep)})
    geo = {}
    for ctry, m, nn, q_lat, q_lon in rows("""select txn_country, count(*), count(lat),
            quantile_cont(lat, [0.05, 0.5, 0.95]), quantile_cont(lon, [0.05, 0.5, 0.95])
            from t group by 1 order by 1"""):
        geo[ctry] = {"rows": m, "lat_long_filled_pct": pct(nn, m),
                     "lat_p05_p50_p95": [round(x, 2) for x in q_lat] if nn else None,
                     "lon_p05_p50_p95": [round(x, 2) for x in q_lon] if nn else None}
    record("labels", "lat_long_by_transaction_country", geo)
    amt = {}
    for cur, m, nn in rows("select currency, count(*), count(amount_usd) from t group by 1 order by 1"):
        amt[cur] = {"rows": m, "amount_usd_filled_pct": pct(nn, m)}
    record("labels", "amount_usd_fill_by_currency", amt)
    print("p95 rule:", RESULTS["labels"]["p95_rule"]["precision_pct"],
          RESULTS["labels"]["p95_rule"]["recall_pct"])


# -------------------------------------------------------------------- signals
def build_features():
    c = con()
    if one("select count(*) from information_schema.tables where table_name = 'f'")[0]:
        return
    hb = HOUR_BUCKET_H
    print("building prior-history features ...")
    c.execute(f"""
        create table f0 as
        select *,
          row_number() over w_c - 1 n_prior,
          -- amount vs own history in the same currency (prior rows only)
          count(*) over (w_cc rows between unbounded preceding and 1 preceding) n_prior_cur,
          avg(ln(greatest(amount, 0.01))) over (w_cc rows between unbounded preceding and 1 preceding) la_mean,
          stddev_samp(ln(greatest(amount, 0.01))) over (w_cc rows between unbounded preceding and 1 preceding) la_sd,
          median(amount) over (w_cc rows between unbounded preceding and 1 preceding) a_med,
          -- first-time merchant / category / country / channel / hour bucket
          case when merchant_name is null then null
               else row_number() over (partition by customer_id, merchant_name order by ts, transaction_id) - 1 end n_prior_same_merchant,
          case when merchant_name is null then null
               else count(merchant_name) over (w_c rows between unbounded preceding and 1 preceding) end n_prior_named,
          case when merchant_category is null then null
               else row_number() over (partition by customer_id, merchant_category order by ts, transaction_id) - 1 end n_prior_same_mcc,
          case when merchant_category is null then null
               else count(merchant_category) over (w_c rows between unbounded preceding and 1 preceding) end n_prior_mcc_named,
          row_number() over (partition by customer_id, txn_country order by ts, transaction_id) - 1 n_prior_same_country,
          row_number() over (partition by customer_id, channel order by ts, transaction_id) - 1 n_prior_same_channel,
          row_number() over (partition by customer_id, hour(ts) // {hb} order by ts, transaction_id) - 1 n_prior_same_hour_bucket,
          -- usual location: mean of prior lat/long
          count(lat) over (w_c rows between unbounded preceding and 1 preceding) n_prior_geo,
          avg(lat) over (w_c rows between unbounded preceding and 1 preceding) lat_mean,
          avg(lon) over (w_c rows between unbounded preceding and 1 preceding) lon_mean,
          -- bursts (range frame includes the row and same-timestamp peers: minus 1)
          count(*) over (partition by customer_id order by ts
                         range between interval {BURST_SHORT_MIN} minutes preceding and current row) - 1 n_short,
          count(*) over (partition by customer_id order by ts
                         range between interval {BURST_LONG_MIN} minutes preceding and current row) - 1 n_long
        from t
        window w_c as (partition by customer_id order by ts, transaction_id),
               w_cc as (partition by customer_id, currency order by ts, transaction_id)""")
    c.execute("""
        create table f1 as select *,
          case when n_prior_cur >= {mh} and la_sd > 0
               then (ln(greatest(amount, 0.01)) - la_mean) / la_sd end amount_z,
          case when n_prior_cur >= {mh} and a_med > 0 then amount / a_med end amount_ratio,
          case when lat is not null and n_prior_geo >= {mh}
               then 2 * 6371 * asin(sqrt(pow(sin(radians(lat - lat_mean) / 2), 2)
                    + cos(radians(lat)) * cos(radians(lat_mean)) * pow(sin(radians(lon - lon_mean) / 2), 2)))
          end dist_km
        from f0""".format(mh=MIN_HISTORY))
    c.execute("drop table f0")
    q = SIGNAL_PERCENTILE
    z_thr, r_thr, d_thr = one(f"""select quantile_cont(amount_z, {q}), quantile_cont(amount_ratio, {q}),
        quantile_cont(dist_km, {q}) from f1 where part = 'fit'""")
    record("signals", "fitted_thresholds", {"amount_z_p95_fit": round(z_thr, 4),
                                            "amount_ratio_p95_fit": round(r_thr, 4),
                                            "distance_km_p95_fit": round(d_thr, 2)})
    mh = MIN_HISTORY
    # Each signal: NULL when undefined, else boolean.
    c.execute(f"""
        create table f as select part, ts, transaction_id, is_fraud, fraud_score, n_prior,
          case when amount_z is not null then amount_z >= {z_thr} end amount_z_high,
          case when amount_ratio is not null then amount_ratio >= {r_thr} end amount_ratio_high,
          case when n_prior_named >= {mh} then n_prior_same_merchant = 0 end first_merchant,
          case when n_prior_mcc_named >= {mh} then n_prior_same_mcc = 0 end first_merchant_category,
          case when acct_country is not null then txn_country <> acct_country end country_not_account_country,
          case when n_prior >= {mh} then n_prior_same_country = 0 end first_country,
          case when dist_km is not null then dist_km >= {d_thr} end far_from_usual_location,
          case when n_prior >= {mh} then n_prior_same_hour_bucket = 0 end first_hour_bucket,
          case when n_prior >= {mh} then n_prior_same_channel = 0 end first_channel,
          n_short >= 1 burst_10m,
          n_long >= {BURST_LONG_N} burst_60m
        from f1""")
    c.execute("drop table f1")


SIGNALS = {
    "amount_z_high": "z-score of ln(amount) vs the customer's prior transactions in the same currency >= FIT p95 (needs >= 5 prior in that currency)",
    "amount_ratio_high": "amount / median of the customer's prior amounts in the same currency >= FIT p95 (needs >= 5 prior in that currency)",
    "first_merchant": "merchant_name never seen before for the customer (needs a merchant name and >= 5 prior named transactions)",
    "first_merchant_category": "merchant_category never seen before for the customer (needs a category and >= 5 prior categorized transactions)",
    "country_not_account_country": "transaction_country (normalized) differs from customers.country (normalized); defined for every row",
    "first_country": "transaction_country never seen before for the customer (needs >= 5 prior)",
    "far_from_usual_location": "haversine distance from the mean prior lat/long >= FIT p95 (needs lat/long and >= 5 prior geo-tagged transactions)",
    "first_hour_bucket": "4-hour bucket of the day never used before by the customer (needs >= 5 prior)",
    "first_channel": "channel never used before by the customer (needs >= 5 prior)",
    "burst_10m": f">= 1 other transaction of the customer in the previous {BURST_SHORT_MIN} minutes",
    "burst_60m": f">= {BURST_LONG_N} other transactions of the customer in the previous {BURST_LONG_MIN} minutes",
}


def signals():
    print("== 2. candidate signals ==")
    build_features()
    record("signals", "definitions", SIGNALS)
    record("signals", "params", {"min_history": MIN_HISTORY, "signal_percentile": SIGNAL_PERCENTILE,
                                 "hour_bucket_hours": HOUR_BUCKET_H,
                                 "history_order": "transaction_date, then transaction_id (tie-break)",
                                 "history_scope": "all dev transactions of the customer strictly before the scored one, any product, any status"})
    # Sparse history.
    hist = {}
    for part in ("fit", "report"):
        m, low, f_low, f_all = one(f"""select count(*), sum((n_prior < {MIN_HISTORY})::int),
            sum((is_fraud and n_prior < {MIN_HISTORY})::int), sum(is_fraud::int) from f where part = '{part}'""")
        hist[part] = {"rows_with_lt5_prior_pct": pct(low, m),
                      "fraud_with_lt5_prior_pct": pct(f_low, f_all)}
    ncu, lowc = one(f"""select count(*), sum((n < {MIN_HISTORY})::int) from
        (select customer_id, count(*) n from t group by 1)""")
    hist["customers_with_lt5_dev_txns_pct"] = pct(lowc, ncu)
    hist["customers_with_dev_txns"] = ncu
    hist["median_dev_txns_per_customer"] = one(
        "select median(n) from (select count(*) n from t group by customer_id)")[0]
    record("signals", "history", hist)
    print("history:", hist)

    out = {}
    for s in SIGNALS:
        res = {}
        for part in ("fit", "report"):
            m, d, on, f_d, f_on = one(f"""select count(*), count({s}), sum({s}::int),
                sum((is_fraud and {s} is not null)::int), sum((is_fraud and {s})::int)
                from f where part = '{part}'""")
            on = on or 0
            f_on = f_on or 0
            base = f_d / d if d else None
            res[part] = {
                "rows": m, "defined_pct": pct(d, m), "on_pct_of_defined": pct(on, d),
                "base_rate_defined_pct": pct(f_d, d),
                "on": rate_block(f_on, on, base) if base else None,
                "off": rate_block(f_d - f_on, d - on, base) if base else None,
            }
        out[s] = res
        r = res["report"]
        print(f"{s:30s} defined {r['defined_pct']}% on {r['on_pct_of_defined']}% "
              f"lift {r['on'] and r['on']['lift']} {r['on'] and r['on']['lift_ci']}")
    record("signals", "per_signal", out)


# ---------------------------------------------------------------- incremental
def fit_logit(X, y, iters=50, ridge=1e-4):
    """Newton-Raphson logistic regression with a tiny ridge (stdlib + numpy)."""
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -35, 35)))
        g = X.T @ (y - p) - ridge * w
        H = (X * (p * (1 - p))[:, None]).T @ X + ridge * np.eye(len(w))
        step = np.linalg.solve(H, g)
        w += step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


def incremental():
    print("== 3. incremental value given fraud_score ==")
    build_features()
    names = list(SIGNALS)
    cols = ", ".join(f"{s}::int {s}" for s in names)
    data = {}
    for part in ("fit", "report"):
        d = con().execute(f"select is_fraud, fraud_score, {cols} from f where part = '{part}' order by ts, transaction_id").fetchnumpy()
        data[part] = {k: fnum(v) for k, v in d.items()}

    # Score strata: missing + FIT deciles of fraud_score.
    fs_fit = data["fit"]["fraud_score"]
    nf_max = float(np.nanmax(fs_fit[data["fit"]["is_fraud"] == 0]))
    edges = np.append(np.nanquantile(fs_fit, np.linspace(0.1, 0.9, 9)), nf_max)
    n_strata = len(edges) + 2  # missing + len(edges) + 1 score bins

    def strata(fs):
        return np.where(np.isnan(fs), 0, 1 + np.searchsorted(edges, fs, side="right"))

    def design(part, extra):
        fs = data[part]["fraud_score"]
        st = strata(fs)
        X = [np.ones(len(fs))] + [(st == k).astype(float) for k in range(2, n_strata)] + [(st == 0).astype(float)]
        for s in extra:
            v = data[part][s]
            X.append(np.nan_to_num(v, nan=0.0))
            X.append(np.isnan(v).astype(float))
        return np.column_stack(X)

    y_fit = data["fit"]["is_fraud"].astype(bool)
    y_rep = data["report"]["is_fraud"].astype(bool)
    rng = np.random.default_rng(SEED)
    boot = [rng.integers(0, len(y_rep), len(y_rep)) for _ in range(N_BOOT)]

    def model_scores(extra):
        w = fit_logit(design("fit", extra), y_fit.astype(float))
        return design("report", extra) @ w

    base_s = model_scores([])
    base_auc = auc(y_rep, base_s)
    base_boot = np.array([auc(y_rep[b], base_s[b]) for b in boot])
    record("incremental", "method", (
        "Logistic regression (numpy Newton-Raphson, ridge 1e-4) fitted on FIT, scored on REPORT. "
        "Base model: one-hot fraud_score strata (missing, the 10 FIT deciles, and above the FIT "
        "non-fraud maximum). Each candidate adds "
        "the signal and an undefined indicator. delta_auc = AUC(base + signal) - AUC(base) on REPORT, "
        f"95% interval from {N_BOOT} paired bootstrap resamples (seed {SEED}). Stratified lift: "
        "Mantel-Haenszel risk ratio of signal on vs off across the same strata (Greenland-Robins CI)."))
    record("incremental", "score_strata_edges_fit", [round(float(e), 3) for e in edges])
    record("incremental", "base_model_report_auc", round(base_auc, 4))
    record("incremental", "fraud_score_alone_report_auc_missing_as_lowest",
           round(auc(y_rep, np.nan_to_num(data["report"]["fraud_score"], nan=-1.0)), 4))
    record("incremental", "base_model_report_auc_ci",
           [round(float(np.quantile(base_boot, q)), 4) for q in (0.025, 0.975)])
    print("base AUC", base_auc)

    st_rep = strata(data["report"]["fraud_score"])
    out = {}
    for s in names + ["all_signals"]:
        extra = names if s == "all_signals" else [s]
        sc = model_scores(extra)
        a = auc(y_rep, sc)
        deltas = np.array([auc(y_rep[b], sc[b]) for b in boot]) - base_boot
        res = {"auc": round(a, 4), "delta_auc": round(a - base_auc, 4),
               "delta_auc_ci": [round(float(np.quantile(deltas, q)), 4) for q in (0.025, 0.975)]}
        if s != "all_signals":
            v = data["report"][s]
            num = den = vr = 0.0
            for k in range(0, n_strata):
                m = (st_rep == k) & ~np.isnan(v)
                on = m & (v == 1)
                off = m & (v == 0)
                n1, n0 = on.sum(), off.sum()
                a1, b0 = y_rep[on].sum(), y_rep[off].sum()
                N = n1 + n0
                if not n1 or not n0:
                    continue
                num += a1 * n0 / N
                den += b0 * n1 / N
                vr += (n1 * n0 * (a1 + b0) - a1 * b0 * N) / N ** 2
            if num > 0 and den > 0:
                rr = num / den
                se = math.sqrt(vr / (num * den))
                res["mh_risk_ratio"] = round(float(rr), 3)
                res["mh_risk_ratio_ci"] = [round(float(rr * math.exp(-Z95 * se)), 3),
                                           round(float(rr * math.exp(Z95 * se)), 3)]
            else:
                res["mh_risk_ratio"] = None
                res["mh_risk_ratio_ci"] = None
        out[s] = res
        print(f"{s:30s} AUC {res['auc']} delta {res['delta_auc']} {res['delta_auc_ci']} "
              f"MH {res.get('mh_risk_ratio')} {res.get('mh_risk_ratio_ci')}")
    record("incremental", "per_signal", out)


# ---------------------------------------------------------------- conclusions
def conclude():
    flags = {}
    for s in SIGNALS:
        r = RESULTS["signals"]["per_signal"][s]["report"]
        inc = RESULTS["incremental"]["per_signal"][s]
        lift_lo = r["on"]["lift_ci"][0] if r["on"] and r["on"]["lift_ci"] else None
        d_lo = inc["delta_auc_ci"][0]
        expected = (r["on"]["n"] * r["base_rate_defined_pct"] / 100) if r["on"] else 0
        if (r["defined_pct"] or 0) < SPARSE_DEFINED_PCT or expected < SPARSE_EXPECTED_FRAUD:
            flag = "undefined_too_sparse"
        elif lift_lo is not None and lift_lo >= USEFUL_LIFT_LOW and d_lo > 0:
            flag = "useful"
        elif (lift_lo is not None and lift_lo > 1.0) or d_lo > 0:
            flag = "weak"
        else:
            flag = "none"
        flags[s] = flag
    art = RESULTS["labels"]["synthetic_artefact"]
    RESULTS["investigation"] = {
        "flags": flags,
        "rule": FLAG_RULE,
        "has_signal": any(v == "useful" for v in flags.values()),
        "label_is_synthetic_artefact": art["non_fraud_with_score_above_non_fraud_max"] == 0
        and art["fraud_with_score_above_non_fraud_max"] > 0,
    }
    print("flags:", flags, "has_signal:", RESULTS["investigation"]["has_signal"])


# ---------------------------------------------------------------------- verify
def hash_groups():
    groups = [("customers.csv", [os.path.join(RAW, "customers.csv")])]
    for g in DEV_MONTH_GLOBS:
        groups.append((f"transactions/{g}", sorted(glob.glob(os.path.join(RAW, "transactions", g)))))
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


MODES = {"labels": labels, "signals": signals, "incremental": incremental}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "summary"
    if mode == "verify":
        verify()
    if mode == "hashes":
        for name, nf, nr, hx in hash_groups():
            print(f"| {nf} | {nr:,} | {hx} | {name} |")
        return
    if mode == "summary":
        for f in MODES.values():
            f()
        conclude()
        RESULTS.update({"script_version": SCRIPT_VERSION, "window": WINDOW,
                        "window_start": WIN_START, "window_end": WIN_END,
                        "held_out_cut": HELD_OUT_CUT,
                        "split": {"fit": [WIN_START, SPLIT], "report": [SPLIT, WIN_END],
                                  "note": "half-open intervals on transaction_date"}})
        with open(os.path.join(BASE, "summary.json"), "w", encoding="utf-8") as fh:
            json.dump(RESULTS, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print("wrote summary.json")
        return
    if mode not in MODES:
        raise SystemExit(__doc__)
    MODES[mode]()


if __name__ == "__main__":
    main()
