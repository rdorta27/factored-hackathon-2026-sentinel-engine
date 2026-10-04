# Data manifest — Customer 360 transaction signals, development zone

Generated 2026-10-04 with script `2026-10-04+c360-dev-signals-v1`. Data is
read in place from the data engine's raw CSVs (`sentinel-data-engine/data/raw/`,
gitignored) and never copied into this folder. `customers.csv` and every
transaction partition hash the same as in [`../dev-v1/MANIFEST.md`](../dev-v1/MANIFEST.md),
so both runs measure the same snapshot. Products and complaints are not read.

Only partitions with `process_date < 2025-07-01` are listed and read. Nothing
at or after the held-out cut was downloaded for this run.

## Verify

```bash
# from this folder; SENTINEL_RAW_DIR is optional when the raw data sits at
# <repo>/sentinel-data-engine/data/raw
SENTINEL_RAW_DIR=/abs/path/to/sentinel-data-engine/data/raw \
  python3 measure_customer_signals.py verify   # every line must print OK
```

Rows are CSV records (`csv.DictReader`, utf-8-sig); the hash is sha256 over
the file bytes in sorted path order, first 16 hex characters.

| Files | Rows | sha256[:16] | Pattern (under raw/) |
|---|---|---|---|
| 1 | 150,000 | c5bb1f835d688b61 | customers.csv |
| 198 | 801,170 | 35b2ea1fca446fe5 | transactions/year=2023/month=*/day=*/*.csv |
| 366 | 1,471,814 | 92a382c13753b5a7 | transactions/year=2024/month=*/day=*/*.csv |
| 31 | 122,056 | 4404624bc10a227d | transactions/year=2025/month=01/day=*/*.csv |
| 28 | 110,632 | 67ed5c40f9150c88 | transactions/year=2025/month=02/day=*/*.csv |
| 31 | 123,365 | fe498c7e2fa647d1 | transactions/year=2025/month=03/day=*/*.csv |
| 30 | 120,838 | d176aed461cfc76e | transactions/year=2025/month=04/day=*/*.csv |
| 31 | 126,679 | e383f45133801f10 | transactions/year=2025/month=05/day=*/*.csv |
| 30 | 118,998 | 26af781504f3d54e | transactions/year=2025/month=06/day=*/*.csv |

Partition total is 2,995,552 transactions. The event-date filter
`[2023-06-01, 2025-07-01)` keeps `labels.n_dev`; the difference is the rows
dated 2025-07-01 that sit in the 2025-06-30 partition.

## Method

- **Engine.** DuckDB 1.1.3 and numpy (both already present), in memory. No
  scikit-learn or scipy: the logistic regression (Newton-Raphson), AUC
  (Mann-Whitney with tied ranks), Wilson intervals and the Mantel-Haenszel
  risk ratio are written out in the script.
- **Population.** Every development transaction of every customer (no
  sampling): all types, channels and statuses, since `is_fraud` is set on all
  of them. Only `customer_id` and `country` are read from `customers.csv`.
- **Split.** FIT = `[2023-06-01, 2025-01-01)`, REPORT = `[2025-01-01,
  2025-07-01)` on `transaction_date` (`split`). Thresholds, percentiles,
  score strata and model weights come from FIT; every headline number is on
  REPORT. FIT-part rates are reported too, for stability.
- **No future peeking.** Customer history is every development transaction
  of the same customer strictly before the scored one, ordered by
  `transaction_date` then `transaction_id` (window frames ending at
  `1 preceding`). History therefore starts at 2023-06-01, which is why FIT
  has many rows with short history (`signals.history.fit`).
- **Country spelling.** `transaction_country` "Mexico" is mapped to "México"
  (`labels.country_normalization`); `customers.country` already uses
  "México" only.
- **Amount.** Compared with the customer's history in the same currency on
  `amount`, not `amount_usd`: `amount_usd` is empty for every USD row and for
  about 5% of ARS/COP rows (`labels.amount_usd_fill_by_currency`), and a
  same-currency comparison needs no conversion.
- **Decision 010 rule.** Re-derived exactly as
  `evidence/evaluation/eval_measure.py::account_thresholds` does it (p95 by
  account country and charge currency, groups of at least 100), on FIT, and
  applied with a strict `>` as `sentinel-ai-core/app/policy/engine.py` does.
- **Incremental value.** Base model = one-hot `fraud_score` strata (missing,
  FIT deciles, above the FIT non-fraud maximum). Each signal adds itself plus
  an undefined indicator. Paired bootstrap (200 resamples, seed 20261004) on
  REPORT rows fetched in a fixed order, so `summary.json` is byte-identical
  across runs.
- **Flags.** The rule is a constant in the script and copied into
  `investigation.rule`.
