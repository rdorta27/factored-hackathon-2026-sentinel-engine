# Customer 360 transaction signals (development zone, 2026-10-04)

Second Customer 360 run. [dev-v1](../dev-v1/README.md) found no usable signal
in product status, pre-authorization pairs, duplicates or complaint history.
This run checks what remains for a "dispute investigation" feature:
deterministic, charge-time signals that say whether a charge is unusual for
the customer, and whether they add anything to `fraud_score` and the p95
handoff rule of [decision 010](../../../docs/build/decisions/010-fraud-handoff-rule.md).

| File | What it is |
|---|---|
| `measure_customer_signals.py` | Exact script used (DuckDB + numpy, both already present). Modes `labels`, `signals`, `incremental`, `summary`, `verify`. |
| `summary.json` | The evidence: aggregates and flags only. **Cite this, never hand-copied numbers.** |
| `MANIFEST.md` | Data hashes (`verify` reference) and the method of each check |

Window: development zone, event dates in `[2023-06-01, 2025-07-01)`. Temporal
split inside it (`split`): thresholds, percentiles and model weights are fitted
on FIT `[2023-06-01, 2025-01-01)`; every number below is on REPORT
`[2025-01-01, 2025-07-01)` unless it says FIT. All customers, no sampling.
Signals use only the customer's transactions strictly before the scored one;
`is_fraud` is the label, never a feature.

## Conclusions (flags in `summary.json`)

`investigation.has_signal` is **`false`**. No signal is `useful` or `weak`.

| Signal (`investigation.flags.*`) | Flag | Why |
|---|---|---|
| `amount_z_high`, `amount_ratio_high` | `none` | Defined for almost every charge, lift interval contains 1, no AUC gain over the score (`signals.per_signal.<s>.report.on.lift_ci`, `incremental.per_signal.<s>.delta_auc_ci`). |
| `country_not_account_country`, `first_country` | `none` | Same: lift interval around 1, delta AUC interval around 0. |
| `first_hour_bucket`, `first_channel` | `none` | Point lift below 1, interval reaches 1; no AUC gain. |
| `first_merchant`, `first_merchant_category` | `undefined_too_sparse` | Computable on fewer than 20% of charges (`report.defined_pct`): `merchant_name` is empty on most rows. Where defined, lift is still around 1. |
| `far_from_usual_location` | `undefined_too_sparse` | Needs lat/long, present on about 19% of rows (`labels.lat_long_by_transaction_country`), and México coordinates are noise around (0, 0), not places. |
| `burst_10m`, `burst_60m` | `undefined_too_sparse` | Almost never fires (`report.on_pct_of_defined`): fewer than 5 frauds expected among the flagged rows, so it cannot be tested. |

Label sanity (section 1):

- **Prevalence** is about 0.1% (`labels.prevalence_pct`,
  `labels.prevalence_report`) and flat across country, currency, channel,
  type, status, hour, and whether score, merchant or lat/long are present
  (`labels.levels_with_lift_ci_excluding_1`: 2 of 58 levels, about what
  chance gives). Frauds per customer match a Poisson draw
  (`labels.fraud_per_customer`). The label behaves as an independent random
  draw at about 0.1%.
- **`fraud_score` is the only field that carries the label.** AUC on scored
  rows (`labels.fraud_score_auc.report.scored_rows`); about 20% of rows of
  both classes have no score (`labels.fraud_score_distribution.*.score_missing_pct`).
- **Synthetic artefact** (`labels.synthetic_artefact`,
  `investigation.label_is_synthetic_artefact` = `true`): non-fraud scores
  never exceed 30.0 and fraud scores spread up to 100, so any score above 30
  is fraud with certainty. `is_fraud` is not a deterministic function of one
  field (below 30 the classes overlap, and unscored frauds exist), but its
  only signal is this generator boundary.
- **Decision 010 p95 rule**, re-derived on FIT
  (`labels.p95_rule.thresholds_fit`, about 28.5 in every group): it fires on
  about 4% of REPORT charges with precision `labels.p95_rule.precision_pct`
  (about 1.4%) and recall `labels.p95_rule.recall_pct` (about 55%). A rule at
  the FIT non-fraud maximum (`labels.bound_rule`) reaches about the same
  recall at 100% precision on about 0.05% of charges. That number is an
  artefact of the generator, not a property a bank score would have; it shows
  that the p95 handoff here is a workload choice, as decision 010 already
  says.

Incremental value (section 3): the base model (score strata only) scores
`incremental.base_model_report_auc`; adding any single signal, or all of them
(`incremental.per_signal.all_signals`), changes AUC by less than its bootstrap
interval, and every interval contains 0. The stratified Mantel-Haenszel risk
ratios (`incremental.per_signal.<s>.mh_risk_ratio_ci`) contain 1 for every
testable signal. `burst_10m` shows a large ratio from a single fraud and is
flagged too sparse.

History coverage: on REPORT only `signals.history.report.rows_with_lt5_prior_pct`
(about 1%) of charges have fewer than 5 prior transactions; the FIT share is
higher only because history starts at the window start. About
`signals.history.customers_with_lt5_dev_txns_pct` (about 1.6%) of customers
never reach 5 transactions in the window.

## Recommendation

The data gives no support for an "unusual for you" fraud investigation: no
customer-relative signal predicts `is_fraud`, alone or on top of
`fraud_score`, and the label itself is a synthetic draw whose only
information is the score boundary. The assistant may still state **facts**
computed from prior history, because they are true regardless of fraud
labels: "you have paid at this merchant before" / "this is the first time
this merchant appears on your account" (only when `merchant_name` is
present), "this charge was made in another country than your account", "this
amount is higher than your usual in this currency". These must be phrased as
descriptions that help the customer recognize the charge, never as a fraud
judgment or a risk level. In the advisor handoff the same facts can be listed
as context next to the decision 010 rule id, again without a risk claim.
Do not use: distance from usual location (México coordinates are not
places), bursts (they do not occur), and any score or weighting built from
these signals, which would add noise to the existing rule. The escalation
logic should stay as decision 010 defines it.

## What this run cannot measure

- Whether any signal would help on real bank data: the label carries no
  structure to learn from, so "none" here means "this dataset cannot show
  it", not "the signal is useless".
- Customer-facing accuracy of the factual statements is guaranteed by
  construction (they are computed from the same history the customer sees),
  but whether they help a customer recognize a charge needs user testing.
- Merchant signals for the ~77% of charges without `merchant_name`.

## Caveats

- Flags come from the rule fixed in code (`investigation.rule`); they are
  thresholds on intervals, not formal multiple-testing-corrected tests.
- Lift intervals are Wilson intervals on the signal-on rate divided by the
  defined-row base rate (base treated as fixed).
- Ties in `transaction_date` are broken by `transaction_id`; the burst count
  uses a time range and counts same-second peers as prior.

## How to cite

Reference `summary.json` fields directly (e.g. `investigation.has_signal`,
`labels.p95_rule.precision_pct`). Raw data is never committed, and
`summary.json` holds no identifiers, merchant names or individual amounts.

## Reproduce

```bash
python3 measure_customer_signals.py verify    # must print OK on every line
python3 measure_customer_signals.py summary   # regenerates summary.json (byte-identical)
```

Set `SENTINEL_RAW_DIR` when the raw data is not at
`<repo>/sentinel-data-engine/data/raw`. A full run takes about three minutes.

## Immutability rule

This folder is write-once. A new run goes in a new folder under
`evidence/customer-360/`.
