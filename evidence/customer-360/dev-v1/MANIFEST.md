# Data manifest — Customer 360, development zone

Generated 2026-10-04 with script `2026-10-04+c360-dev-v1`. Data is read in
place from the data engine's raw CSVs (`sentinel-data-engine/data/raw/`,
gitignored) and never copied into this folder. The two snapshots hash the
same as in [`../../flows/2024Q4-v3/MANIFEST.md`](../../flows/2024Q4-v3/MANIFEST.md),
so both runs measure the same snapshot.

Only partitions with `process_date < 2025-07-01` are listed and read. Nothing
at or after the held-out cut was downloaded for this run.

## Verify

```bash
# from this folder; SENTINEL_RAW_DIR is optional when the raw data sits at
# <repo>/sentinel-data-engine/data/raw
SENTINEL_RAW_DIR=/abs/path/to/sentinel-data-engine/data/raw \
  python3 measure_customer_360.py verify   # every line must print OK
```

Rows are CSV records (`csv.DictReader`, utf-8-sig); the hash is sha256 over
the file bytes in sorted path order, first 16 hex characters.

| Files | Rows | sha256[:16] | Pattern (under raw/) |
|---|---|---|---|
| 1 | 400,000 | f071906b4342b35f | products.csv |
| 1 | 150,000 | c5bb1f835d688b61 | customers.csv |
| 198 | 801,170 | 35b2ea1fca446fe5 | transactions/year=2023/month=*/day=*/*.csv |
| 366 | 1,471,814 | 92a382c13753b5a7 | transactions/year=2024/month=*/day=*/*.csv |
| 31 | 122,056 | 4404624bc10a227d | transactions/year=2025/month=01/day=*/*.csv |
| 28 | 110,632 | 67ed5c40f9150c88 | transactions/year=2025/month=02/day=*/*.csv |
| 31 | 123,365 | fe498c7e2fa647d1 | transactions/year=2025/month=03/day=*/*.csv |
| 30 | 120,838 | d176aed461cfc76e | transactions/year=2025/month=04/day=*/*.csv |
| 31 | 126,679 | e383f45133801f10 | transactions/year=2025/month=05/day=*/*.csv |
| 30 | 118,998 | 26af781504f3d54e | transactions/year=2025/month=06/day=*/*.csv |
| 198 | 12,078 | 5f45316d9ae1a209 | complaints/year=2023/month=*/day=*/*.csv |
| 366 | 22,329 | d5b8202886ec017a | complaints/year=2024/month=*/day=*/*.csv |
| 31 | 1,998 | 3f1ab9001b4e5741 | complaints/year=2025/month=01/day=*/*.csv |
| 28 | 1,745 | c478ca3fedac2693 | complaints/year=2025/month=02/day=*/*.csv |
| 31 | 1,764 | 3c7b3517147b06c3 | complaints/year=2025/month=03/day=*/*.csv |
| 30 | 1,797 | 3a9a41abc29f1987 | complaints/year=2025/month=04/day=*/*.csv |
| 31 | 1,876 | 313bc0dc0bd8ab5f | complaints/year=2025/month=05/day=*/*.csv |
| 30 | 1,825 | 1780c2303d02ad9c | complaints/year=2025/month=06/day=*/*.csv |

Partition totals are 2,995,552 transactions and 45,412 complaints. The event-
date filter `[2023-06-01, 2025-07-01)` keeps `products.n_transactions_dev` and
`complaints.n_dev`; the difference is the rows dated 2025-07-01 that sit in
the 2025-06-30 partition (the synthetic one-day offset described in
[`../../flows/2024Q4-v3/method.md`](../../flows/2024Q4-v3/method.md)).

## Method

- **Engine.** DuckDB 1.1.3 (already a dependency of `sentinel-data-engine`
  and `sentinel-ai-core`), in memory. All columns are read as text, trimmed,
  and cast (`decimal(18,2)` for money, `timestamp` for dates).
- **Window.** Whole development zone on event dates (`transaction_date`,
  `creation_date`). Products: `last_updated < 2025-07-01` (327,035 kept,
  72,965 excluded, as in flows v3).
- **Customers.** Only `customer_id` and `country` are read, to break products
  down by country and to test orphans. No other field of the PII table is read.
- **A. Products.** Counts, duplicates, nulls, distributions by country,
  `credit_limit` fill by type, products per customer, orphans both ways.
- **B. Balance.** Joined per product with its development transactions.
  A product is *contradictory* if any of these holds: a transaction currency
  differs from the product currency; a negative balance; a credit card
  balance above its limit; `last_transaction_date` is missing or more than one
  day earlier than a transaction dated before the snapshot's `last_updated`;
  or, for deposit-type products (savings, checking, debit card) whose
  `last_updated` is after every development movement, the implied opening
  balance (`balance - approved deposits + all other approved movements`) is
  negative. That last test is deliberately lenient: every non-deposit counts
  as an outflow. *Undetermined* means the snapshot predates the product's own
  latest movement, so no balance check is possible. Spearman rank correlation
  (per currency) tests whether balances follow net flow.
- **C. Status.** Transaction status mix; transactions by product status;
  Pending followed within 7 days by an Approved/Reversed with the same
  product, merchant and amount (baseline: the same test anchored on Approved);
  exact duplicates (all fields but the ID) and near duplicates (same product,
  merchant, amount within ±10 minutes).
- **D. Complaints.** Header fields that could name a charge; fill and
  resolution of `affected_product_id`; ownership (does the product belong to
  the complainant); exact and ±1% amount match against a transaction in the
  90 days before `creation_date`, on the affected product and on any product
  of the complainant. Baseline: the same test with the claimed amount of the
  next complaint in `complaint_id` order (chance level).
- Thresholds and flag rules are constants in the script and are copied into
  `balance.rule` and `complaints.rule`.
