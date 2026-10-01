# Tasks

## 1. Evidence: thresholds by account country and currency

- [x] 1.1 Extend `evidence/evaluation/eval_measure.py` (new script version) to read `silver_transactions`, `silver_customers` and `silver_products` from the pipeline DuckDB file (`SENTINEL_EVIDENCE_DUCKDB`), join charges to the customer's country, normalize `Mexico` to `México` as a guard, and report amount and fraud-score percentiles per country and charge currency, product share per country and currency and a minimum group size. Area: [data](../../../docs/build/areas/data.md), [ml](../../../docs/build/areas/ml.md). Verify: unit test on a synthetic in-memory sample shows two currencies of one country reported as separate groups.
- [x] 1.2 Run it on the local `gold_bank.duckdb` (gitignored) and freeze `evidence/evaluation/2024Q4-v2/summary.json` (aggregates only, held-out rows 0). Decisions 25, 26. Verify: `verify` mode passes on the new run and v1 is unchanged (`git diff evidence/evaluation/2024Q4-v1` empty).

## 2. Policy configuration per currency

- [x] 2.1 Change the loader and engine to read `values` per currency and look up the charge currency; a missing key or null does not fire; equal does not fire. Area: [ai](../../../docs/build/areas/ai.md). Verify: tests for the USD-on-MX-account, per-currency fraud score, missing currency and equal-value scenarios in `tests/test_policy*.py`.
- [x] 2.2 Fill `config/policy/{mx,co,ar}.yaml` with p95 values per currency from 2024Q4-v2, each with its `source`, and leave groups below 100 charges empty. Decisions 25, 26. Verify: a test checks every value whose `source` is an evidence run matches the cited `summary.json` field, and a value with a bank `source` is checked for format only.
- [x] 2.3 Record the policy file version and the synthetic flag on every `decide` record. Area: [ai](../../../docs/build/areas/ai.md). Verify: an observability test changes a value between two turns and sees two versions.

## 3. Inputs to the rules

- [x] 3.1 Carry `fraud_score` on Gold rows (mock and DuckDB adapter) and on the candidate; never in listings, replies or model requests. Area: [ai](../../../docs/build/areas/ai.md). Verify: `tests/test_gold_duckdb.py` and a test that the transactions listing and the router request whitelist exclude the score.
- [x] 3.2 Report the not-mine claim from the keyword baseline and the router output, pass it to the engine, and cite `fraud.claim` with its handoff mapping and es-419 and pt-BR texts. Decision 25. Verify: tests for "no fui yo", "não fui eu" (claim, `fraud.claim`) and "no reconozco este cargo" (no claim).
- [ ] 3.3 Give each demo customer a local-currency and a USD product, with charges above each configured value; the MX MXN product has no threshold and keeps the other rules. Area: [ai](../../../docs/build/areas/ai.md). Verify: test that every configured country and currency has a mock row above its value.

## 4. Evaluation and demo evidence

- [ ] 4.1 Add eval cases: one per rule and shown currency, plus the not-mine claim in es-419 and pt-BR, in `sentinel-ai-core/eval/cases/`. Area: [ml](../../../docs/build/areas/ml.md). Verify: the runner replays them with the expected handoff outcome.
- [ ] 4.2 Freeze a new evaluation run and a new adversarial run (`SENTINEL_WRITE_EVIDENCE=1`) as soon as groups 1 to 3 are done, without waiting for decision 10. Verify: new folders under `evidence/evaluation-runs/` and `evidence/adversarial/`, unsafe outcomes still zero.

## 5. Documentation and decisions

- [x] 5.1 Write the account-country and product-currency assumptions once in `docs/understand/dataset.md` citing the data dictionary (`customers.country`, `products.currency`, `transaction_country`), with `México` as the canonical name; link it from REQ-0013 and the delivery script. Area: [data](../../../docs/build/areas/data.md). Verify: links resolve.
- [ ] 5.2 Record decisions 25 and 26 as files in `docs/build/decisions/` (per-currency p95, workload rationale, evidence run), move them to decided in `team/pending-decisions.md`, and add to decision 15 that there are no Brazilian accounts (data dictionary). Verify: decision files exist and the pending table no longer lists 25 and 26.
- [ ] 5.3 Update the REQ-0006 card and status, the `team/tasks.md` row, and the docs that cite the old single-value thresholds (`docs/architecture/specification.md` decision priority). Verify: `grep -rn "high_amount" docs` shows the per-currency form only.
- [ ] 5.4 Fill the measured values and group limitations from 2024Q4-v2 into `docs/rationale/policy-thresholds.md` (method already written) by citing `summary.json` fields, and remove its pending status line. Verify: the page cites the run and no value is typed by hand.
