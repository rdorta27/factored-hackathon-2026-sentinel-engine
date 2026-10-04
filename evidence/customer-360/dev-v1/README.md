# Customer 360 data evidence, first run (development zone, 2026-10-04)

Measures whether the LATAM Bank dataset can support two planned "Customer
360" reads, both used as **evidence while investigating a disputed charge**,
not as new conversation topics:

1. **Products:** type, status, currency, `current_balance`, `credit_limit`,
   with an as-of date.
2. **History:** recent transactions plus the customer's complaint history.

[Decision 008](../../../docs/build/decisions/008-account-inquiry-scope.md)
warned that the product snapshot is biased, and
[decision 003](../../../docs/build/decisions/003-disputes-flow.md) measured 0%
linkage from complaints to interactions. This run checks both before the
plans are written.

| File | What it is |
|---|---|
| `measure_customer_360.py` | Exact script used (DuckDB, already a project dependency) |
| `summary.json` | The evidence: aggregates and flags only. **Cite this, never hand-copied numbers.** |
| `MANIFEST.md` | Data hashes (`verify` reference) and the method of each check |

Window: the whole development zone, event dates in `[2023-06-01, 2025-07-01)`
(`window_start`, `window_end`, `held_out_cut`). Products are filtered on
`last_updated < 2025-07-01`, as in [flows v3](../../flows/2024Q4-v3/README.md).

## Conclusions (flags in `summary.json`)

| Flag | Value | Why |
|---|---|---|
| `balance.safe_to_show` | `false` | The snapshot has no usable as-of date (`balance.asof_usable`: `last_updated` precedes the product's own latest movement for `balance.asof_last_updated_before_latest_txn_pct`), balances do not follow net flow (`balance.spearman_by_currency.*.deposit_balance_vs_net_flow` is negative in every currency), and `last_transaction_date` never equals a real transaction (`balance.last_transaction_date_equals_a_txn_pct`). Only `balance.plausibly_coherent_pct` of products can be checked and pass. |
| `complaints.charge_linkable` | `false` | Complaints have no transaction, merchant or charge-date field (`complaints.charge_reference_fields`); claimed amounts match a prior transaction no better than a shuffled amount (`complaints.amount_match`). |
| `complaints.product_linkable` | `false` | `affected_product_id` always resolves but never belongs to the complainant (`complaints.affected_product_owned_by_complainant_pct`), and its currency usually differs from the claimed currency. |
| `complaints.customer_linkable` | `true` | Every complaint resolves to a customer (`complaints.orphan_complaint_to_customer_pct`). |
| `status.non_active_products_have_txns` | `false` | Blocked, Closed and Suspended products carry no transactions and no `last_transaction_date` (`status.products_by_status_full_snapshot`). There is no status-change date (`status.status_change_date_available`). |

What this means for scope:

- **Products:** expose type, status, currency and `credit_limit`. Do not
  show `current_balance` next to movements: the two disagree and there is no
  date to explain the gap. If a balance is ever shown, label it as an
  unreconciled snapshot value with no as-of date.
- **Status as a signal:** "a charge on a blocked card" never happens in this
  data, so product status cannot explain a disputed charge. Pending
  transactions are never followed by a matching Approved or Reversed
  (`status.pending_followed_pct`), so the pre-authorization explanation is not
  supported, and there are no exact or near duplicate charges
  (`status.exact_duplicate_rows_pct`, `status.near_duplicate_rows_pct`), even
  though the dictionary announces ~2% duplicates.
- **Complaint history:** usable only as customer-level context (count, dates,
  category, status). It cannot be attached to the disputed charge or to the
  customer's own product.

Other findings worth knowing:

- No product is in MXN: every product of a México customer is in USD
  (`products.by_country.México.currency`), although the dictionary lists MXN.
- 18% of development transactions belong to products whose snapshot row is
  dated after the cut (`products.txn_product_not_in_dev_snapshot_pct`); a
  Customer 360 read restricted to the development snapshot misses them.
- Transaction-to-product and product-to-customer links are complete
  (`products.orphan_txn_to_product_pct`,
  `products.txn_customer_mismatch_product_owner_pct`).

## Caveats

- `safe_to_show` and `charge_linkable` come from rules fixed in code and
  copied into `balance.rule` and `complaints.rule`. They are thresholds on
  rates, not statistical tests.
- The balance check is lenient on purpose (every non-deposit counts as an
  outflow), so `balance.contradictory_pct` is a lower bound.
- `status.dictionary_duplicate_noise_pct` is the dictionary's stated figure,
  not a measurement.

## How to cite

Reference `summary.json` fields directly (e.g. `balance.safe_to_show`,
`complaints.amount_match.product.within_1pct_match_pct`). Raw data is never
committed. Dataset values in Spanish are kept as-is: *Cuenta Ahorro* =
savings account; *Cuenta Corriente* = checking account; *Tarjeta Crédito* /
*Tarjeta Débito* = credit / debit card; *Préstamo Personal* / *Préstamo
Hipotecario* = personal loan / mortgage; *Inversión* = investment; *Seguro* =
insurance; *Cargo no reconocido* = unrecognized charge.

## Reproduce

```bash
python3 measure_customer_360.py verify    # must print OK on every line
python3 measure_customer_360.py summary   # regenerates summary.json
```

Set `SENTINEL_RAW_DIR` when the raw data is not at
`<repo>/sentinel-data-engine/data/raw`. A full run takes a few minutes.

## Immutability rule

This folder is write-once. A new run goes in a new folder under
`evidence/customer-360/`.
