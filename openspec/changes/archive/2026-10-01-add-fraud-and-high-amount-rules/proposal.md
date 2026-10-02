# Proposal

## Why

REQ-0006 (P0, In progress) stays open because the fraud and high-amount handoff rules exist in the policy engine but never fire: their thresholds are null (pending decisions 25 and 26), `fraud_score` never reaches the candidate, and nothing sets the customer's "it was not me" claim. The v1 reference percentiles cannot set them: they group by `transaction_country` (where a purchase happened) and pool currencies.

The data dictionary settles two facts the rules depend on. Accounts belong only to Mexico, Colombia and Argentina (`customers.country`). Currency belongs to the product (`products.currency`: MXN, COP, ARS, USD), so a customer can hold local and USD accounts; a single-currency threshold skips every USD charge.

## What Changes

- Thresholds for both rules are set per account country **and per charge currency**: `fraud_score` and `high_amount` each hold one value per currency (for example MX: MXN and USD). A currency without a value does not fire that rule. **BREAKING** for the policy file format (`thresholds.*.value` becomes a per-currency map).
- A new write-once evidence run, `evidence/evaluation/2024Q4-v2/`, reports percentiles by account country and charge currency and product currency shares. Country names are normalized to the canonical `México`, `Colombia`, `Argentina`.
- Values are synthetic, from the development window (p95, at least 100 charges per group), cite their source, and a bank replaces them by configuration; decisions 25 and 26 are closed in `docs/build/decisions/`.
- `fraud_score` travels from Gold (mock and DuckDB) to the candidate the engine reads.
- The understanding step reports an explicit "not mine" claim (for example "no fui yo", "não fui eu"; ordinary "no reconozco este cargo" is not one) and the engine hands it off as `fraud.claim`.
- The three-country and per-product-currency assumptions are written once in `docs/understand/dataset.md`, citing the data dictionary, and linked from REQ-0013, decision 15 and the delivery script.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `policy-engine`: thresholds become per country and currency; a currency without a value does not fire.
- `decision-priority`: suspected fraud also fires on the "not mine" claim; thresholds are looked up by the charge currency.
- `evaluation-evidence`: reference thresholds are grouped by account country and charge currency.
- `gold-layer`: rows carry `fraud_score`; demo customers may hold charges in USD besides their local currency.
- `llm-router`: the understanding output carries the "not mine" claim; the fraud score never goes to the model.
- `observability`: decisions record the policy file version.

## Impact

- Code: `sentinel-ai-core/app/policy/` (engine, loader), `config/policy/{mx,co,ar}.yaml`, `app/tools/gold.py`, `app/tools/gold_duckdb.py`, the baseline and router output, the Gold mock.
- Evidence: new `evidence/evaluation/2024Q4-v2/`; new evaluation and adversarial runs, since frozen runs never change.
- Docs: `docs/understand/dataset.md`, decisions 25 and 26 (new files in `docs/build/decisions/`), `team/pending-decisions.md` (decisions 15, 25, 26), REQ-0006 and REQ-0013 cards.
- Requirements: REQ-0006, REQ-0049, REQ-0041, REQ-0013, REQ-0031.

## Non-goals

- Staleness threshold (decision 27): stays off; the as-of date is always stated (REQ-0039).
- Repeat-dispute and blocked-product rules (P11, P12): need data the service view does not expose.
- Any claim of fraud-detection accuracy: a percentile sets advisor workload, not precision.
