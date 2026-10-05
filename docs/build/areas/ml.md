---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Machine Learning

**Evaluation criterion:** model selection, optimization, implementation and tracking. **Owner:** Rubén.

**Requirements:** the `ml` rows in the [requirements table](../../requirements/requirements.md).

**Related:** [dataset](../../understand/dataset.md), [metrics](../metrics.md), [metrics report](../metrics-report.md), [evidence index](../../../evidence/README.md).

## Scope

- One **learned component**, compared with a **baseline** on a sealed held-out set (REQ-0016).
- **Prompt-injection defense**, together with the access control in [security](../security.md).
- **Experiment tracking:** each evaluation run is one write-once folder ([013](../decisions/013-experiment-tracking.md)).

## The learned component: an intent router

The learned component is a **prompted LLM that labels the intent of a customer message** ([007](../decisions/007-learned-component.md), [016](../decisions/016-router-models.md)). It is not a dispute-category classifier. Decision 007 first named the dispute category as the target. The served router labels the intent, the language and the "not mine" claim ([016](../decisions/016-router-models.md)).

| Item | Value |
|---|---|
| Input | The customer message, with personal data masked. The model does not receive ids, the fraud score or Gold rows ([what the model never receives](../../rationale/model-data-minimization.md)). |
| Output | One of four intents (`charge`, `missing`, `out_of_scope`, `person`), the language and the "not mine" claim. The output is bounded JSON. |
| Model | GLM 5.3 Flash on Fireworks AI, on both routes ([016](../decisions/016-router-models.md)). |
| Served version | `router_v2`: a prompt with 8 examples from the development split. |
| Baseline | A keyword classifier (`DemoModel`). The service also uses it as the per-turn fallback when the model fails. |
| Confidence | The router reports a confidence per label. The cut-offs come from [`2024Q4-calibration-v1`](../../../evidence/evaluation-runs/2024Q4-calibration-v1/summary.json) (`cutoffs.t_act`, `cutoffs.t_abstain`). They are off by default. |

The model labels the intent only. Code decides permissions, policy, confirmations and handoffs ([decision priority](../../../openspec/specs/decision-priority/spec.md)).

## Result

Source: [`2024Q4-eval-v7`](../../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json). The [metrics report](../metrics-report.md) gives the full tables.

- `router_v2` is more accurate than the baseline on the same 280 sealed cases. The 95% interval of the paired net difference is above zero (`component.paired.*`).
- Most of the gain is in the `missing` intent: a vague message that needs a clarifying question (`component.versions.<version>.breakdown.by_intent`).
- The four language variants (es-MX, es-CO, es-AR, pt-BR) give about the same accuracy (`component.versions.router_v2.breakdown.by_variant`).
- 0 unsafe outcomes on 75 attacks. With the rule of three, the true rate is at most 4% (95% confidence).

## Data that we did not use as a label

The team checked each dataset label before the choice ([flow selection](../flows/03-flow-selection.md)):

| Candidate label | Why we did not use it | Evidence |
|---|---|---|
| `complaints.category` | `description` contains the category in 100% of complaints. This is a label leak. | [flow selection](../flows/03-flow-selection.md) |
| Call transcripts | The transcripts are templates. | [flow selection](../flows/03-flow-selection.md) |
| `was_escalated` | No call field separates it. The spread is 0.65% to 1.59%. | [flow measurements](../flows/02-flow-measurements.md) |
| `is_fraud` | The label has no structure. A `fraud_score` above 30 is always fraud, which is an artefact of the data generator. No customer signal adds information to `fraud_score`. | [`dev-signals-v1`](../../../evidence/customer-360/dev-signals-v1/README.md): `investigation.has_signal`, `investigation.label_is_synthetic_artefact` |

For this reason the cases are **team-written text in es-419 and pt-BR**, declared as simulation (REQ-0031). A label comes from the design of the case. It does not come from a dataset column.

## Rigor

- **Split by unit.** All variants of one base stay on one side: development, validation or held-out.
- **Sealed before the measurement.** A hash seals the held-out set. The runner refuses a second measurement of the same seal.
- **Isolated author.** The author of the held-out set did not read the prompt, the examples or the development cases.
- **Examples from development only.** `build_examples` refuses an example from validation or held-out.
- **Time split for dataset labels.** The cut is 2025-07-01. The leak check is in `evidence/evaluation/method.md`.
- **Trained baseline.** It trains on development only and tunes on validation only. Training stops with an error that names any held-out case. The validation scores describe only. The claim comes from the single sealed measurement. If the trained baseline ties or beats the router there, the report says so.
- **Intervals.** A cluster bootstrap over bases gives the intervals. An interval wider than ±10 points is "descriptive" and decides nothing.

## Evidence

| Item | Status | Where |
|---|---|---|
| Component against baseline on the same held-out set | Done | [`2024Q4-eval-v7`](../../../evidence/evaluation-runs/2024Q4-eval-v7/summary.json) |
| Error analysis by intent, variant and noise | Done | [metrics report](../metrics-report.md), sections 3 to 5 |
| Experiment log | Done | One folder per run in [`evidence/evaluation-runs/`](../../../evidence/evaluation-runs/) ([013](../decisions/013-experiment-tracking.md)) |
| Adversarial set and results | Done | [`evidence/adversarial/`](../../../evidence/adversarial/) and the attack block of `eval-v7` |
| Confidence cut-offs | Done, off by default | [`2024Q4-calibration-v1`](../../../evidence/evaluation-runs/2024Q4-calibration-v1/summary.json) |
| Greetings and small talk | Open | [router v3 plan](../../../team/router-v3-plan.md) |
| A trained baseline (TF-IDF and logistic regression) | Trained and frozen. Not yet measured on the sealed set | [`2024Q4-train-v1`](../../../evidence/evaluation-runs/2024Q4-train-v1/summary.json). The `eval-v8` measurement compares it with the router. |
| Precision, recall and F1 per intent, with intervals | Done in the runner | `per_intent` in each version of a run summary (`eval/per_intent.py`) |
