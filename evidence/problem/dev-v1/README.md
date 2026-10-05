---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Problem evidence, first run (development zone)

This run measures the problem behind the chosen workflow. It answers four
questions with numbers:

1. How many calls end at the first contact, for each reason for the call.
2. How many calls arrive on a busy day, for each candidate workflow.
3. How many agent hours each candidate workflow uses in one month.
4. How much data is missing in the fields that these measures use.

Data type: **Dataset**. The dataset is synthetic. The window is the
development zone, event dates in `[2023-06-17, 2025-07-01)`. The script does
not read an event dated 2025-07-01 or later.

| File | What it is |
|---|---|
| `measure_problem.py` | The script that makes the measures. |
| `summary.json` | The evidence: aggregates only. Cite a field, never a hand-copied number. |
| `MANIFEST.md` | The data hashes for `verify` and the method of each measure. |
| `test_measure_problem.py` | Unit checks of the helper functions on a small fixture. |

The raw data stays outside git, in the data engine's `data/raw/` folder. The
script reads it in place and copies nothing.

## Mapping: reason for the call to candidate workflow

The product field is empty on about 60% of transactional calls
([008](../../../docs/build/decisions/008-account-inquiry-scope.md)). The
mapping therefore uses the reason for the call only. `contact_reason` and
`reason_category` hold the same value on every row, so the table lists the
value once.

| Reason (`contact_reason` / `reason_category`) | Candidate workflow | Why |
|---|---|---|
| Transaccional | Account or payment inquiry | Transactional calls: balances, movements, and declined, pending or reversed payments. The chosen flow enters here. |
| Producto | Card support | Product questions. The data does not separate cards from other products, so this is a coarse proxy. |
| Queja | Transaction dispute | Complaint calls. The dispute flow handles a charge that the customer does not recognize. |
| Técnico | Other | Technical support. It matches no candidate workflow. |
| Comercial | Other | Commercial or sales calls. It matches no candidate workflow. |
| Retención | Other | Retention calls. It matches no candidate workflow. |

No reason maps to **Credit information**. The call data has no credit or loan
reason, so the demand for that workflow is not measurable here.

The mapping is a judgment. A different mapping can change the ranking. This
run reports the ranking under the mapping above. It also lists each reason
that maps to `other`.

## Measures

- **First-contact resolution (FCR).** A call is solved at the first contact
  when `was_resolved` is true. The dataset does not tell if the customer
  called again, so FCR is the dataset field only. Each rate has its count and
  a 95% range (Wilson).
- **Calls per day.** For each workflow: the mean, a busy-day level and the
  highest day. The busy-day level is the 95th percentile of the daily counts:
  95 of 100 days are below it. Each of the last two has a 95% range from a
  bootstrap over the days.
- **Agent hours.** For each workflow: calls in the window times the mean
  handling time. The result is hours per month, ranked from high to low.
  Calls without a duration are counted and are not filled.
- **Missing values.** The share of blank values in `contact_reason`,
  `reason_category`, `was_resolved` and `duration_seconds`.

Every measure uses the development zone only.

## How to run

```bash
# SENTINEL_RAW_DIR is optional when the raw data sits at
# <repo>/sentinel-data-engine/data/raw
SENTINEL_RAW_DIR=/abs/path/to/sentinel-data-engine/data/raw \
  python3 measure_problem.py summary   # writes summary.json
SENTINEL_RAW_DIR=/abs/path/to/sentinel-data-engine/data/raw \
  python3 measure_problem.py verify    # every line must print OK
```

Requires `duckdb`, a dependency of `sentinel-data-engine` and
`sentinel-ai-core`.
