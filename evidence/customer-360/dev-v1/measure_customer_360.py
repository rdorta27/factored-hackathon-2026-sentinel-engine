#!/usr/bin/env python3
"""Customer 360 data-support measurements (products, balance, status, complaints).

First run (v1). Answers two scope questions before planning "Customer 360"
reads used as evidence while investigating a disputed charge:

  1. Can `current_balance` be shown next to listed movements without giving a
     materially incorrect answer (is the balance coherent with transactions)?
  2. Can complaint history be tied to a specific charge, or only to a
     product / customer?

Reads the raw CSVs of the data engine (gitignored, never committed):
  <RAW>/products.csv, <RAW>/customers.csv            (snapshots)
  <RAW>/transactions/year=YYYY/month=MM/day=DD/*.csv (process_date partitions)
  <RAW>/complaints/year=YYYY/month=MM/day=DD/*.csv
RAW defaults to <repo>/sentinel-data-engine/data/raw and can be overridden
with the SENTINEL_RAW_DIR environment variable (absolute path).

Window: the whole development zone, event dates in [2023-06-01, 2025-07-01).
Only partitions with process_date < 2025-07-01 are globbed (event dates are
equal to or one day later than process_date, so no development row is lost)
and every row is then filtered on its event date. Snapshot rows are filtered
on `last_updated < 2025-07-01` (the same filter as evidence/flows/2024Q4-v3);
the excluded count is reported. No fact row at/after the held-out cut is read.
The only snapshot-wide figures (all 400,000 product rows) are integrity
counts: rows_snapshot, duplicate_*, orphan_* and
status.products_by_status_full_snapshot (status and fill counts only).

customers.csv holds synthetic PII; only `customer_id` and `country` are read
and only aggregates leave this script. summary.json never holds identifiers,
rows, names or amounts of individual records.

Usage:
    python3 measure_customer_360.py products | balance | status | complaints
    python3 measure_customer_360.py summary   # all four + summary.json
    python3 measure_customer_360.py verify    # recompute MANIFEST hashes

Requires duckdb (a dependency of sentinel-data-engine and sentinel-ai-core).
"""
import csv
import glob
import hashlib
import json
import os
import sys

import duckdb

SCRIPT_VERSION = "2026-10-04+c360-dev-v1"
HELD_OUT_CUT = "2025-07-01"
WINDOW = "dev"
WIN_START = "2023-06-01"
WIN_END = HELD_OUT_CUT  # exclusive

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

DEPOSIT_TYPES = ("Cuenta Ahorro", "Cuenta Corriente", "Tarjeta Débito")
CREDIT_TYPES = ("Tarjeta Crédito", "Préstamo Personal", "Préstamo Hipotecario")
CARD = "Tarjeta Crédito"

# Tolerances / windows (fixed in code, reported in summary.json).
PENDING_FOLLOW_DAYS = 7      # Pending -> later Approved/Reversed pair window
NEAR_DUP_MINUTES = 10        # near-duplicate charge window
COMPLAINT_LOOKBACK_DAYS = 90 # charge must precede complaint by <= 90 days
CONTRADICTION_MAX_PCT = 5.0  # balance flag threshold
LINK_LIFT_MIN = 2.0          # complaint match rate must beat baseline by 2x

RESULTS = {}


def record(mode, key, value):
    RESULTS.setdefault(mode, {})[key] = value


def pct(a, b):
    return round(100.0 * a / b, 2) if b else None


def files_for(table):
    out = []
    for g in DEV_MONTH_GLOBS:
        out.extend(sorted(glob.glob(os.path.join(RAW, table, g))))
    if not out:
        raise SystemExit(f"no {table} partitions under {RAW} -- sync raw data first")
    return out


_CON = None


def con():
    """One in-memory DuckDB with dev-filtered views/tables."""
    global _CON
    if _CON is not None:
        return _CON
    for f in ("products.csv", "customers.csv"):
        if not os.path.exists(os.path.join(RAW, f)):
            raise SystemExit(f"missing {f} under {RAW}")
    c = duckdb.connect()
    rd = "header=true, all_varchar=true"
    c.execute(f"""
        create table p_all as
        select trim(product_id) product_id, trim(customer_id) customer_id,
               trim(product_type) product_type, trim(product_number) product_number,
               trim(currency) currency,
               try_cast(nullif(trim(current_balance), '') as decimal(18,2)) current_balance,
               try_cast(nullif(trim(credit_limit), '') as decimal(18,2)) credit_limit,
               try_cast(nullif(trim(opening_date), '') as date) opening_date,
               trim(product_status) product_status,
               try_cast(nullif(trim(last_transaction_date), '') as timestamp) last_transaction_date,
               try_cast(nullif(trim(last_updated), '') as timestamp) last_updated
        from read_csv('{os.path.join(RAW, "products.csv")}', {rd})""")
    c.execute(f"create table p as select * from p_all where last_updated < timestamp '{HELD_OUT_CUT}'")
    c.execute(f"""
        create table cu as
        select trim(customer_id) customer_id, trim(country) country
        from read_csv('{os.path.join(RAW, "customers.csv")}', {rd})""")
    c.execute(f"""
        create table t_raw as
        select trim(transaction_id) transaction_id,
               try_cast(transaction_date as timestamp) ts,
               trim(product_id) product_id, trim(customer_id) customer_id,
               trim(transaction_type) transaction_type,
               try_cast(amount as decimal(18,2)) amount, trim(currency) currency,
               nullif(trim(merchant_name), '') merchant_name,
               trim(transaction_status) transaction_status
        from read_csv({files_for("transactions")!r}, {rd}, union_by_name=true)""")
    c.execute(f"""create table t as select * from t_raw
        where ts >= timestamp '{WIN_START}' and ts < timestamp '{WIN_END}'""")
    c.execute(f"""
        create table c_raw as
        select trim(complaint_id) complaint_id,
               try_cast(creation_date as timestamp) created,
               trim(customer_id) customer_id, trim(case_type) case_type,
               trim(category) category, trim(subcategory) subcategory,
               nullif(trim(affected_product_id), '') affected_product_id,
               nullif(trim(origin_interaction_id), '') origin_interaction_id,
               try_cast(nullif(trim(claimed_amount), '') as decimal(18,2)) claimed_amount,
               nullif(trim(currency), '') currency
        from read_csv({files_for("complaints")!r}, {rd}, union_by_name=true)""")
    c.execute(f"""create table cmp as select * from c_raw
        where created >= timestamp '{WIN_START}' and created < timestamp '{WIN_END}'""")
    _CON = c
    return c


def one(sql):
    return con().execute(sql).fetchone()


def rows(sql):
    return con().execute(sql).fetchall()


# --------------------------------------------------------------------------- A
def products():
    print("== A. products ==")
    n_all, = one("select count(*) from p_all")
    n_dev, = one("select count(*) from p")
    record("products", "rows_snapshot", n_all)
    record("products", "rows_dev", n_dev)
    record("products", "rows_excluded_heldout", n_all - n_dev)
    print(f"snapshot rows {n_all}, dev (last_updated < cut) {n_dev}")

    dup_id, dup_num = one("""select count(*) - count(distinct product_id),
                                    count(*) - count(distinct product_number) from p_all""")
    record("products", "duplicate_product_id", dup_id)
    record("products", "duplicate_product_number", dup_num)

    nulls = {}
    for col in ("product_id", "customer_id", "product_type", "currency",
                "current_balance", "product_status", "opening_date",
                "last_transaction_date", "last_updated"):
        n, = one(f"select count(*) - count({col}) from p")
        nulls[col] = n
    record("products", "nulls_dev", nulls)
    print("nulls (dev):", nulls)

    def dist(col):
        return {k: v for k, v in rows(f"select {col}, count(*) from p group by 1 order by 1")}

    record("products", "product_type", dist("product_type"))
    record("products", "product_status", dist("product_status"))
    record("products", "currency", dist("currency"))

    by_country = {}
    for country, col, val, n in rows("""
        select coalesce(cu.country, '(no customer)'), k, v, count(*) from (
            select customer_id, 'product_type' k, product_type v from p
            union all select customer_id, 'product_status', product_status from p
            union all select customer_id, 'currency', currency from p) x
        left join cu using (customer_id) group by all order by all"""):
        by_country.setdefault(country, {}).setdefault(col, {})[val] = n
    record("products", "by_country", by_country)
    cur_country = {k: v["currency"] for k, v in by_country.items()}
    print("currency by country:", cur_country)

    fill = {}
    for ptype, n, nl in rows("""select product_type, count(*), count(credit_limit)
                                from p group by 1 order by 1"""):
        fill[ptype] = {"n": n, "credit_limit_filled": nl, "fill_pct": pct(nl, n)}
    record("products", "credit_limit_fill_by_type", fill)
    print("credit_limit fill:", {k: v["fill_pct"] for k, v in fill.items()})

    ppc = {str(k): v for k, v in rows("""
        select case when n >= 5 then '5+' else n::varchar end b, count(*)
        from (select customer_id, count(*) n from p group by 1) group by 1 order by 1""")}
    record("products", "customers_by_product_count_dev", ppc)
    n_cust, = one("select count(*) from cu")
    with_prod, = one("select count(distinct customer_id) from p_all")
    record("products", "customers_total", n_cust)
    record("products", "customers_without_products_pct", pct(n_cust - with_prod, n_cust))

    orph, = one("select count(*) from p_all left join cu using (customer_id) where cu.customer_id is null")
    record("products", "orphan_product_to_customer_pct", pct(orph, n_all))
    n_t, = one("select count(*) from t")
    o_all, = one("select count(*) from t left join p_all using (product_id) where p_all.product_id is null")
    o_dev, = one("select count(*) from t left join p using (product_id) where p.product_id is null")
    cust_mis, = one("select count(*) from t join p_all using (product_id) where t.customer_id <> p_all.customer_id")
    record("products", "n_transactions_dev", n_t)
    record("products", "orphan_txn_to_product_pct", pct(o_all, n_t))
    record("products", "txn_product_not_in_dev_snapshot_pct", pct(o_dev, n_t))
    record("products", "txn_customer_mismatch_product_owner_pct", pct(cust_mis, n_t))
    print(f"txns {n_t}: orphan vs snapshot {pct(o_all, n_t)}%, "
          f"product missing from dev snapshot {pct(o_dev, n_t)}%, owner mismatch {pct(cust_mis, n_t)}%")


# --------------------------------------------------------------------------- B
def balance():
    print("== B. balance coherence ==")
    c = con()
    dep = ", ".join(f"'{x}'" for x in DEPOSIT_TYPES)
    c.execute(f"""
        create or replace table agg as
        select product_id,
               count(*) n_tx, min(ts) first_tx, max(ts) last_tx,
               count(*) filter (where t.currency <> p.currency) cur_mismatch,
               sum(amount) filter (where transaction_status = 'Approved'
                                   and transaction_type = 'Deposit') dep_in,
               sum(amount) filter (where transaction_status = 'Approved'
                                   and transaction_type <> 'Deposit') dep_out,
               sum(amount) filter (where transaction_status = 'Approved'
                                   and transaction_type = 'Purchase') purchases,
               sum(amount) filter (where transaction_status = 'Approved'
                                   and transaction_type = 'Payment') payments,
               sum(amount) filter (where transaction_status = 'Approved') gross,
               max(ts) filter (where ts <= p.last_updated) last_tx_before_asof
        from t join p using (product_id) group by 1""")
    c.execute(f"""
        create or replace table b as
        select p.*, agg.* exclude (product_id),
          (product_type in ({dep})) is_deposit,
          (product_type = '{CARD}') is_card
        from p join agg using (product_id)""")
    n, = one("select count(*) from b")
    record("balance", "products_with_txns", n)

    # As-of usability.
    asof_before_last, ltd_null, ltd_contra, tx_before_open = one("""
        select count(*) filter (where last_updated < last_tx),
               count(*) filter (where last_transaction_date is null),
               count(*) filter (where last_tx_before_asof is not null
                                and (last_transaction_date is null
                                     or last_transaction_date < last_tx_before_asof - interval 1 day)),
               count(*) filter (where first_tx < opening_date)
        from b""")
    record("balance", "asof_last_updated_before_latest_txn_pct", pct(asof_before_last, n))
    record("balance", "last_transaction_date_null_pct", pct(ltd_null, n))
    record("balance", "last_transaction_date_contradicts_txns_pct", pct(ltd_contra, n))
    record("balance", "first_txn_before_opening_date_pct", pct(tx_before_open, n))
    print(f"products with txns {n}; last_updated before latest txn {pct(asof_before_last, n)}%; "
          f"last_transaction_date contradicts txns {pct(ltd_contra, n)}%; "
          f"txn before opening {pct(tx_before_open, n)}%")

    # Is last_transaction_date derived from the transactions at all?
    m_ltd, exact_ltd, day_ltd = one(f"""
        select count(*),
          count(*) filter (where exists (select 1 from t where t.product_id = b.product_id
                                          and t.ts = b.last_transaction_date)),
          count(*) filter (where exists (select 1 from t where t.product_id = b.product_id
                                          and t.ts::date = b.last_transaction_date::date))
        from b where last_transaction_date >= timestamp '{WIN_START}'
                 and last_transaction_date < timestamp '{WIN_END}'""")
    record("balance", "last_transaction_date_checkable", m_ltd)
    record("balance", "last_transaction_date_equals_a_txn_pct", pct(exact_ltd, m_ltd))
    record("balance", "last_transaction_date_same_day_as_a_txn_pct", pct(day_ltd, m_ltd))
    print(f"last_transaction_date equals a txn timestamp {pct(exact_ltd, m_ltd)}% "
          f"(same day {pct(day_ltd, m_ltd)}%) of {m_ltd}")

    cur_bad, = one("select count(*) from b where cur_mismatch > 0")
    record("balance", "currency_mismatch_product_vs_txn_pct", pct(cur_bad, n))

    neg = {k: v for k, v in rows("""select product_type, count(*) filter (where current_balance < 0)
                                    from p group by 1 order by 1""")}
    record("balance", "negative_balance_by_type_dev", neg)
    zero_bal = {k: pct(z, m) for k, z, m in rows("""
        select product_type, count(*) filter (where current_balance = 0), count(*)
        from p group by 1 order by 1""")}
    record("balance", "zero_balance_pct_by_type_dev", zero_bal)

    n_card, over, nolim = one("""select count(*) filter (where product_type = 'Tarjeta Crédito'),
            count(*) filter (where product_type = 'Tarjeta Crédito' and current_balance > credit_limit),
            count(*) filter (where product_type = 'Tarjeta Crédito' and credit_limit is null) from p""")
    record("balance", "card_balance_over_limit_pct", pct(over, n_card))
    record("balance", "card_credit_limit_null_pct", pct(nolim, n_card))

    # Magnitude test on deposit-type products whose snapshot is after every
    # dev movement (so all observed movements are already in the balance).
    # Lenient: every approved non-deposit counts as an outflow, so the implied
    # opening balance (balance - inflow + outflow) is as large as possible.
    n_dep, implied_neg, bal_lt_in = one("""
        select count(*),
               count(*) filter (where current_balance - coalesce(dep_in,0) + coalesce(dep_out,0) < 0),
               count(*) filter (where current_balance < coalesce(dep_in,0) - coalesce(dep_out,0))
        from b where is_deposit and last_updated >= last_tx""")
    record("balance", "deposit_products_asof_after_txns", n_dep)
    record("balance", "deposit_implied_opening_negative_pct", pct(implied_neg, n_dep))

    # Rank correlation: if balances were derived from movements, they would
    # track the net flow / gross flow; independent generation gives ~0.
    def spearman(where, x):
        r, = one(f"""
            select corr(rx, ry) from (
              select rank() over (order by {x}) rx,
                     rank() over (order by current_balance) ry
              from b where {where})""")
        return round(r, 3) if r is not None else None

    sp = {}
    for cur, in rows("select distinct currency from b order by 1"):
        sp[cur] = {
            "deposit_balance_vs_net_flow": spearman(
                f"is_deposit and currency = '{cur}'", "coalesce(dep_in,0) - coalesce(dep_out,0)"),
            "deposit_balance_vs_gross_flow": spearman(
                f"is_deposit and currency = '{cur}'", "coalesce(gross,0)"),
            "card_balance_vs_purchases_minus_payments": spearman(
                f"is_card and currency = '{cur}'", "coalesce(purchases,0) - coalesce(payments,0)"),
        }
    record("balance", "spearman_by_currency", sp)
    print("spearman:", sp)

    # Per-product verdict.
    contra, = one("""
        select count(*) from b where
            cur_mismatch > 0
            or current_balance < 0
            or (is_card and credit_limit is not null and current_balance > credit_limit)
            or (last_tx_before_asof is not null and (last_transaction_date is null
                or last_transaction_date < last_tx_before_asof - interval 1 day))
            or (is_deposit and last_updated >= last_tx
                and current_balance - coalesce(dep_in,0) + coalesce(dep_out,0) < 0)""")
    undetermined, = one("""select count(*) from b where last_updated < last_tx
                           and not (last_tx_before_asof is not null and (last_transaction_date is null
                                or last_transaction_date < last_tx_before_asof - interval 1 day))
                           and cur_mismatch = 0 and current_balance >= 0
                           and not (is_card and credit_limit is not null and current_balance > credit_limit)""")
    record("balance", "contradictory_pct", pct(contra, n))
    record("balance", "undetermined_asof_before_txns_pct", pct(undetermined, n))
    record("balance", "plausibly_coherent_pct", pct(n - contra - undetermined, n))
    asof_usable = pct(asof_before_last, n) is not None and pct(asof_before_last, n) < CONTRADICTION_MAX_PCT
    # A balance derived from movements must rise with net inflow (deposit
    # accounts). Gross flow only measures account size, so it does not count.
    net = [d["deposit_balance_vs_net_flow"] for d in sp.values()
           if d["deposit_balance_vs_net_flow"] is not None]
    tracks = bool(net) and min(net) >= 0.3
    safe = (pct(contra, n) < CONTRADICTION_MAX_PCT) and asof_usable and tracks
    record("balance", "asof_usable", asof_usable)
    record("balance", "balance_tracks_movements", tracks)
    record("balance", "safe_to_show", safe)
    record("balance", "rule", (
        f"safe_to_show = contradictory_pct < {CONTRADICTION_MAX_PCT} and "
        f"asof_last_updated_before_latest_txn_pct < {CONTRADICTION_MAX_PCT} and "
        "spearman deposit_balance_vs_net_flow >= 0.3 in every currency"))
    print(f"contradictory {pct(contra, n)}%, undetermined {pct(undetermined, n)}%, safe_to_show={safe}")


# --------------------------------------------------------------------------- C
def status():
    print("== C. status signals ==")
    c = con()
    n, = one("select count(*) from t")
    record("status", "n_transactions_dev", n)
    st = {k: v for k, v in rows("select transaction_status, count(*) from t group by 1 order by 1")}
    record("status", "transaction_status", st)
    record("status", "transaction_status_pct", {k: pct(v, n) for k, v in st.items()})

    by_ps = {}
    for ps, m, decl, after in rows("""
        select p.product_status, count(*),
               count(*) filter (where transaction_status = 'Declined'),
               count(*) filter (where ts > p.last_updated)
        from t join p using (product_id) group by 1 order by 1"""):
        by_ps[ps] = {"n": m, "declined_pct": pct(decl, m), "after_last_updated_pct": pct(after, m)}
    record("status", "txns_by_product_status", by_ps)
    inactive = sum(v["n"] for k, v in by_ps.items() if k != "Active")
    record("status", "txns_on_blocked_closed_suspended", inactive)
    record("status", "txns_on_blocked_closed_suspended_pct", pct(inactive, n))
    record("status", "status_change_date_available", False)
    # Same question on the whole snapshot (status only, no other field read):
    # do non-Active products ever carry a transaction or a last_transaction_date?
    full = {}
    for ps, m, with_tx, ltd in rows("""
        select product_status, count(*),
               count(*) filter (where product_id in (select product_id from t)),
               count(last_transaction_date)
        from p_all group by 1 order by 1"""):
        full[ps] = {"products": m, "with_dev_txns_pct": pct(with_tx, m),
                    "last_transaction_date_filled_pct": pct(ltd, m)}
    record("status", "products_by_status_full_snapshot", full)
    record("status", "non_active_products_have_txns",
           any(v["with_dev_txns_pct"] for k, v in full.items() if k != "Active"))
    print("by product status:", by_ps)

    # Pre-authorization pattern: Pending followed by Approved/Reversed with
    # the same product, merchant and amount within PENDING_FOLLOW_DAYS.
    # Baseline: the same test anchored on Approved rows (chance repetition).
    def follow_rate(anchor):
        m, hit = one(f"""
            with a as (select transaction_id, product_id, coalesce(merchant_name,'') mer, amount, ts
                       from t where transaction_status = '{anchor}')
            select count(*), count(*) filter (where exists (
                select 1 from t b where b.product_id = a.product_id
                  and coalesce(b.merchant_name,'') = a.mer and b.amount = a.amount
                  and b.transaction_id <> a.transaction_id
                  and b.transaction_status in ('Approved','Reversed')
                  and b.ts > a.ts and b.ts <= a.ts + interval {PENDING_FOLLOW_DAYS} day))
            from a""")
        return m, hit
    m, hit = follow_rate("Pending")
    record("status", "pending_followed_pct", pct(hit, m))
    mb, hitb = follow_rate("Approved")
    record("status", "baseline_approved_followed_pct", pct(hitb, mb))
    record("status", "pending_follow_days", PENDING_FOLLOW_DAYS)
    print(f"pending followed {pct(hit, m)}% vs approved baseline {pct(hitb, mb)}%")

    # Duplicates: exact (all fields but id) and near (same product, merchant,
    # amount within NEAR_DUP_MINUTES).
    exact, = one("""select count(*) - count(distinct (product_id, ts, transaction_type, amount,
                                                       merchant_name, transaction_status)) from t""")
    dup_id, = one("select count(*) - count(distinct transaction_id) from t")
    near, = one(f"""
        select count(*) from t a where exists (
            select 1 from t b where b.product_id = a.product_id
              and coalesce(b.merchant_name,'') = coalesce(a.merchant_name,'')
              and b.amount = a.amount and b.transaction_id <> a.transaction_id
              and b.ts between a.ts - interval {NEAR_DUP_MINUTES} minute
                           and a.ts + interval {NEAR_DUP_MINUTES} minute)""")
    record("status", "duplicate_transaction_id", dup_id)
    record("status", "exact_duplicate_rows_pct", pct(exact, n))
    record("status", "near_duplicate_rows_pct", pct(near, n))
    record("status", "near_duplicate_minutes", NEAR_DUP_MINUTES)
    record("status", "dictionary_duplicate_noise_pct", 2.0)
    print(f"dup id {dup_id}, exact dup {pct(exact, n)}%, near dup {pct(near, n)}%")


# --------------------------------------------------------------------------- D
def complaints():
    print("== D. complaint linkage ==")
    c = con()
    n, = one("select count(*) from cmp")
    record("complaints", "n_dev", n)
    cols = [r[0] for r in c.execute("describe c_raw").fetchall()]
    hdr = sorted(glob.glob(os.path.join(RAW, "complaints", "year=2024", "month=10", "day=01", "*.csv")))
    if hdr:
        with open(hdr[0], newline="", encoding="utf-8-sig") as fh:
            cols = next(csv.reader(fh))
    charge_fields = [x for x in cols if any(k in x for k in (
        "transaction", "merchant", "amount", "product", "charge"))]
    record("complaints", "charge_reference_fields", charge_fields)
    record("complaints", "has_transaction_id_field", any("transaction" in x for x in cols))
    record("complaints", "has_merchant_field", any("merchant" in x for x in cols))

    fp, fa, fc, fo = one("""select count(affected_product_id), count(claimed_amount),
                                   count(currency), count(origin_interaction_id) from cmp""")
    record("complaints", "affected_product_id_fill_pct", pct(fp, n))
    record("complaints", "claimed_amount_fill_pct", pct(fa, n))
    record("complaints", "origin_interaction_id_fill_pct", pct(fo, n))
    claim_fill = {k: pct(a, m) for k, m, a in rows("""
        select case_type, count(*), count(claimed_amount) from cmp group by 1 order by 1""")}
    record("complaints", "claimed_amount_fill_pct_by_case_type", claim_fill)

    res, same_cust, same_cur, both_cur = one("""
        select count(p_all.product_id),
               count(*) filter (where p_all.customer_id = cmp.customer_id),
               count(*) filter (where cmp.currency is not null and p_all.currency = cmp.currency),
               count(*) filter (where cmp.currency is not null and p_all.product_id is not null)
        from cmp left join p_all on p_all.product_id = cmp.affected_product_id
        where cmp.affected_product_id is not null""")
    record("complaints", "affected_product_resolves_pct", pct(res, fp))
    record("complaints", "affected_product_owned_by_complainant_pct", pct(same_cust, fp))
    record("complaints", "claimed_currency_equals_product_currency_pct", pct(same_cur, both_cur))
    cust_orph, = one("select count(*) from cmp left join cu using (customer_id) where cu.customer_id is null")
    record("complaints", "orphan_complaint_to_customer_pct", pct(cust_orph, n))
    print(f"product fill {pct(fp, n)}%, resolves {pct(res, fp)}%, owned by complainant {pct(same_cust, fp)}%")

    # Charge match: an Approved/Pending/Reversed/Declined txn whose amount
    # equals claimed_amount within COMPLAINT_LOOKBACK_DAYS before creation.
    # Baseline: the same test with the claimed amount of the next complaint
    # (deterministic shift by complaint_id order) -> chance level.
    c.execute("""create or replace table cm as
        select *, lead(claimed_amount) over (order by complaint_id) shifted_amount
        from cmp where claimed_amount is not null""")

    def match(scope, amount_col, tol):
        key = ("t.product_id = cm.affected_product_id" if scope == "product"
               else "t.customer_id = cm.customer_id")
        where = "cm.affected_product_id is not null" if scope == "product" else "true"
        amt = (f"t.amount = cm.{amount_col}" if tol is None else
               f"abs(t.amount - cm.{amount_col}) <= {tol} * cm.{amount_col}")
        if tol == "any":
            amt = "true"
        m, hit = one(f"""
            select count(*), count(*) filter (where exists (
                select 1 from t where {key} and {amt}
                  and t.ts <= cm.created
                  and t.ts >= cm.created - interval {COMPLAINT_LOOKBACK_DAYS} day))
            from cm where {where} and cm.{amount_col} is not null""")
        return m, hit

    out = {}
    for scope in ("product", "customer"):
        m, hit = match(scope, "claimed_amount", None)
        mb, hitb = match(scope, "shifted_amount", None)
        m1, hit1 = match(scope, "claimed_amount", 0.01)
        mb1, hitb1 = match(scope, "shifted_amount", 0.01)
        ma, hita = match(scope, "claimed_amount", "any")
        out[scope] = {"n": m, "match_pct": pct(hit, m), "baseline_pct": pct(hitb, mb),
                      "within_1pct_match_pct": pct(hit1, m1),
                      "within_1pct_baseline_pct": pct(hitb1, mb1),
                      "any_txn_in_lookback_pct": pct(hita, ma)}
    record("complaints", "amount_match", out)
    record("complaints", "lookback_days", COMPLAINT_LOOKBACK_DAYS)
    print("amount match:", out)

    cpc = {str(k): v for k, v in rows("""
        select n, count(*) from (select customer_id, count(*) n from cmp group by 1)
        group by 1 order by 1""")}
    record("complaints", "complaints_per_customer", cpc)
    cnr, = one("select count(*) from cmp where subcategory = 'Cargo no reconocido'")
    record("complaints", "cargo_no_reconocido_n", cnr)

    def lift(d):
        best = max(d["match_pct"] or 0, d["within_1pct_match_pct"] or 0)
        base = max(d["baseline_pct"] or 0, d["within_1pct_baseline_pct"] or 0, 0.01)
        return best >= 1.0 and best >= LINK_LIFT_MIN * base
    linkable = lift(out["product"]) or lift(out["customer"])
    record("complaints", "charge_linkable", linkable)
    record("complaints", "product_linkable",
           (pct(same_cust, fp) or 0) >= 95.0)
    record("complaints", "customer_linkable", (pct(cust_orph, n) or 0) <= 5.0)
    record("complaints", "rule", (
        f"charge_linkable = best amount_match rate (exact or within 1%) >= 1% and >= "
        f"{LINK_LIFT_MIN}x its shifted-amount baseline (product or customer scope); product_linkable = "
        "affected_product_owned_by_complainant_pct >= 95"))
    print(f"charge_linkable={linkable}")


# ---------------------------------------------------------------------- verify
def hash_groups():
    groups = [("products.csv", [os.path.join(RAW, "products.csv")]),
              ("customers.csv", [os.path.join(RAW, "customers.csv")])]
    for table in ("transactions", "complaints"):
        for g in DEV_MONTH_GLOBS:
            fs = sorted(glob.glob(os.path.join(RAW, table, g)))
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


MODES = {"products": products, "balance": balance, "status": status, "complaints": complaints}


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
        RESULTS.update({"script_version": SCRIPT_VERSION, "window": WINDOW,
                        "window_start": WIN_START, "window_end": WIN_END,
                        "held_out_cut": HELD_OUT_CUT})
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
