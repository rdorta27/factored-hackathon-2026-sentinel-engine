# Windows and date convention

## Working window: Q4-2024 (development zone)

All four modes measure October–December 2024. Q4-2024 sits inside the
development zone under any defensible cut, so exploring it freely does not
contaminate the final evaluation.

## Held-out: 2025-07 → 2026-06 (70/30 time split)

Adopted cut: **2025-07-01 on event dates**. Development = 2023-06 → 2025-06
(~25/36 months, 70%); held-out = 2025-07 → 2026-06 (~11/36, 30%), final window
June 2026. This follows the ~70/30 worked example in the project docs
(`metrics.md`, `ml.md`). Enforced in code as `HELD_OUT_CUT = "2025-07-01"`
(`date_guard` + snapshot filter).

## Event dates, not partitions (read this before changing WINDOW)

Partitions are by `process_date`, but ~25% of rows carry an event date
(`creation_date` / `interaction_date` / `transaction_date`) one day later
(synthetic offset, measured). Consequences, enforced in code:

- The window is defined on **event dates**: `[2024-10-01, 2025-01-01)`.
- Rows outside it are **excluded and reported** (`[window]` line):
  1,277 transactions + 235 calls + 23 complaints dated 2025-01-01.
- Snapshots (`products.csv`, `customers.csv`) are filtered by `last_updated <
  2025-07-01` (products: kept 327,035 / excluded 72,965).
- `date_guard` fails loudly (well: reports loudly) on any row at/after 2025-07-01.

## Running another window

```bash
python3 measure_flow.py disputes 2025Q1
```

`COMPLAINT_PATS` is built from WINDOW, so complaints follow automatically.
Only do this inside the development zone (< 2025-07-01). Never at/after
2025-07-01 before the final single measurement.
