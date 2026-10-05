---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Model card: the intent router and the trained baseline

This card covers the learned components of the charge-inquiry loop. Each number cites a field of a frozen `summary.json`. The cases are team-written simulation, never dataset rows and never production traffic. The [metrics report](metrics-report.md) gives the full tables. Decision [018](decisions/018-evaluation-acceptance.md) gives the gates.

## Common facts

| Item | Value |
|---|---|
| Task | Label the intent of one customer message: `charge`, `status`, `missing`, `out_of_scope` or `person`. |
| Input | The first message, with personal data masked. The model receives no id, no fraud score and no Gold row. |
| Language | Spanish (es-419) and Brazilian Portuguese (pt-BR). |
| Evaluation | The single measurement [`2024Q4-eval-v8`](../../evidence/evaluation-runs/2024Q4-eval-v8/summary.json): two sealed sets (444 and 92 cases), measured once. |
| Data type | **Simulation.** The cases are model-written. No person wrote or reviewed them ([018](decisions/018-evaluation-acceptance.md#case-provenance-declared-before-sealing)). |
| Served model | `router_v2`. `router_v3` scores higher but fails two gates. |
| Fallback | The keyword baseline answers a turn when the model fails. |

## router_v2 (served)

| Item | Value |
|---|---|
| Type | Prompted LLM, GLM 5.3 Flash on Fireworks AI, both routes ([016](decisions/016-router-models.md)). |
| Prompt | Version `v2`, with 8 examples from the development split (`candidates.router_v2.example_ids`). |
| Output | Intent, language and the "not mine" claim. No subtype, no slot and no draft. |
| Intended use | The served intent router behind `POST /api/v1/chat`. Code decides policy, permission, confirmation and handoff. |
| Kind accuracy | 0.8182 on 308 main cases (`candidates.router_v2.intent.accuracy`). |
| Paired against the keyword baseline | Net +39, interval [0.0617, 0.2045], above zero (`paired.router_v2_vs_baseline`). |
| Unsafe wording | 0 shown (`candidates.router_v2.unsafe_wording`). |
| Cost and latency | USD 0.04141 for 308 calls (`candidates.router_v2.cost_usd.total`); p50/p95 1474.2/4317.14 ms (`latency_ms`). |
| Limits | It emits no subtype, slot or draft, so it cannot serve the full contract-v3 flow. It loses to the trained baseline on this set (below). The `status` intent is weak: it misses every `status` case on the development set ([018](decisions/018-evaluation-acceptance.md#development-baselines-added-2026-10-05)). |

## router_v3 (measured, not served)

| Item | Value |
|---|---|
| Type | Prompted LLM, GLM 5.3 Flash on both routes, prompt version `v3`, with 32 examples (`candidates.router_v3.example_ids`). |
| Output | Intent, subtype, slots and a reply draft. |
| Intended use | The candidate for the contract-v3 flow: subtype labels, slot hints and a checked draft. |
| Kind accuracy | 0.974 on 308 main cases (`candidates.router_v3.intent.accuracy`). |
| Subtype accuracy | 0.8971 (61 of 68) (`candidates.router_v3.subtype.accuracy`). |
| Unsafe wording | 4 of 93 on the main block (`candidates.router_v3.unsafe_wording`). The 4 are drafts the validator rejected, so they were not shown ([018](decisions/018-evaluation-acceptance.md#the-validator-finding)). |
| Verdict | It fails the zero-unsafe-wording gate and the subtype gate, so `router_v2` stays the served model. |
| Limits | The confidence is saturated near 1, so the cut-offs remove correct answers ([cutoff diagnosis](../../evidence/evaluation-runs/2024Q4-cutoff-diagnosis-v1/summary.json)). It is not served. |

## Trained baseline (TF-IDF and logistic regression)

| Item | Value |
|---|---|
| Type | Character n-grams (3 to 5) with TF-IDF and a logistic regression (`2024Q4-train-v1`: `model.type`, `model.ngram_range`, `model.regularization_c` 3.0). |
| Training data | The development split only, 198 cases. It tunes `C` on the validation split (26 cases, descriptive). It reads no held-out case. |
| Model file | `model.json`, sha256 `75f9bef2a3ff53255b879f5b8479baa1de89f93162fb975660c181107322a0c6` (`model.sha256`), 4171 features (`model.features`). |
| Intended use | A research baseline for the learned component. It is not served and it emits no subtype, slot or draft. |
| Kind accuracy | 0.9026 on 308 main cases (`candidates.trained_baseline.intent.accuracy`). |
| Paired against router_v2 | Net +26 for the trained baseline (interval [0.013, 0.1591] for router_v2 minus trained is below zero; the pair `paired.router_v2_vs_trained_baseline` has net -26). |
| Paired against router_v3 | Net +22 for router_v3, interval [0.0097, 0.1364] (`paired.router_v3_vs_trained_baseline`). |
| What it learns | The high-weight character n-grams name each intent: `cobr` (cobro) for charge, `algo` and `blema` (problema) for missing, `sald` (saldo) for out of scope, `ende` (entiende) and `huma` (humano) for person, `ultim` and `estad` (estado) for status (`2024Q4-analysis-v8`: `M2_ngrams.labels`). |
| Limits | It reads the first message only. It has no subtype, slot or draft output. The accuracy on the sealed set (0.9026) is below `router_v3` (0.974) and above the served `router_v2` (0.8182). A cascade of this model then the LLM is a **projection**, not a measurement ([018](decisions/018-evaluation-acceptance.md)). |

## What is real and what is simulation

| Item | Label |
|---|---|
| The cases | **Simulation.** Model-written text, sealed by hash before the run. |
| The model answers | Real live calls to GLM 5.3 Flash under a spend cap. |
| The dataset | Not used as a label. The team checked the dataset labels and rejected them ([ml area](areas/ml.md#data-that-we-did-not-use-as-a-label)). |
| The system outcomes | Simulation over a mock store ([resolution-v2](../../evidence/evaluation-runs/2024Q4-resolution-v2/summary.json)). |
| The cascade and the ROI | **Projection**, not a measurement. |
