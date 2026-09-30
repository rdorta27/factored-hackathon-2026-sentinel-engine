# Method — evaluation evidence

Development window **2024Q4** on event dates: `[2024-10-01, 2025-01-01)`.
Held-out cut **2025-07-01**: only rows strictly before the cut are read and
the held-out count is reported as zero. Partitions are by `process_date`, so
the window is enforced on `creation_date` / `interaction_date` /
`transaction_date` and out-of-window rows are excluded and reported.

`eval_measure.py` reads the gitignored data tree (`evidence/evaluation/data/`
or `evidence/data/`), computes the label universe (`category x subcategory`
for Claim, Complaint and the global history), the Claim mix, claimed-amount
percentiles, nulls and the description leak, the `contact_reason` mix with
escalation/resolution flags, and amount/fraud percentiles per country, then
freezes them as aggregates in `evidence/evaluation/<run-id>/summary.json`.
`verify` recomputes hashes and every field; `derive` pins
`sentinel-ai-core/eval/labels.json` to one frozen run.
