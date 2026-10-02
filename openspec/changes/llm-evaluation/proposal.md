# Proposal

## Why

REQ-0016 (P0, In progress) asks whether the prompted router beats the keyword baseline. Every run so far (`2024Q4-eval-v1` to `v6`) replays fixtures mirrored from the baseline, so the delta is zero by construction. The held-out split has 10 already-measured cases and no metric is reported per country, although Spanish from México, Colombia and Argentina differs in the vocabulary a keyword list misses. This change records real model responses and measures them once on a sealed set sized for each decision, within USD 0.50.

## What Changes

- **Sealed case set:** 70 base situations, each in es-MX, es-CO, es-AR and pt-BR (280 held-out cases), plus 30 development bases × 4, 50 noisy twins and 75 attacks, all team-written simulation. Sealed by hash before measuring; the earlier 10 held-out cases move to development.
- **Real recordings:** each live response is recorded once, keyed by model, prompt version, input and repetition. Cost uses per-model prices (decision [016](../../../docs/build/decisions/016-router-models.md)); output is bounded JSON.
- **Three versions on the same cases:** keyword baseline, router without examples (`v1`) and router with development-only examples (`v2`).
- **Selection on development only:** the cheap and strong models and the route rule are chosen on the development split with the rule in 016. The pt-BR condition becomes a net loss in paired twins.
- **Runner:** metrics per variant (locale and country), paired comparison with cluster-bootstrap intervals, a spend cap, and a refusal to measure a sealed set twice.
- **Rules before results:** each selection or acceptance rule is committed as a Proposed decision before the run that applies it.

## Non-goals

- Changing real Gold or the data pipeline.
- A handoff queue, CRM, MLflow or LLM judge (REQ-0023); scoring is rule-based.
- Re-measuring the sealed set, or using held-out cases as examples.
- Serving the LLM on the public link: it stays on the baseline (decision [012](../../../docs/build/decisions/012-public-deployment.md)).
- Proving strict equivalence between variants; the report states this limit.
- Replacing the keyword `classify` used for the dispute category.

## Capabilities

### New Capabilities

- `sealed-case-set`: authoring of base situations and their four variants, back-translation review (decision [017](../../../docs/build/decisions/017-portuguese.md)), sizing, sealing by hash and the record of measured sets.

### Modified Capabilities

- `llm-router`: recording mode, recordings keyed by model and repetition, per-model cost, bounded output, a prompt version with examples, and a declared route rule.
- `evaluation-runner`: variant fields on cases, per-variant metrics, three-version paired comparison with intervals, stability from recorded repetitions, spend cap and single measurement of a sealed set.

## Impact

- Code: `sentinel-ai-core/app/ai/` and `sentinel-ai-core/eval/`.
- Data: new cases under `eval/cases/` and recordings under `app/ai/fixtures/`, checked for personal data and secrets.
- Evidence: new write-once runs under `evidence/evaluation-runs/`.
- Docs: decision 016 amended, a new decision for acceptance rules, and the REQ-0012, 0013, 0016, 0017, 0020, 0022 and 0024 rows.
- Operations: the API key lives only in the local `.env`; the provider account has a spend limit.
- Schedule: submission is due 2026-10-05; writing and reviewing about 400 variants is the critical path.
