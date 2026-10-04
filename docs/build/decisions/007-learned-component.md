---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 007 · Learned component: prompted LLM classifier

**Date:** 2026-09-29
**Status:** Accepted
**Participants:** Team

## Context

The brief requires at least one learned component, compared with a baseline on the same held-out data, with valid labels and no leakage (REQ-0016, REQ-0017). The [flow selection](../flows/03-flow-selection.md) found three problems:

- No single field separates the target of any of the four flows.
- The complaints have a label leak: `description` contains `category` in every row.
- The transcripts are templates.

We may use approved data only, and we must label team-written data as such (REQ-0031).

## Options

1. **A prompted LLM that classifies the dispute category** (few-shot examples from the development split only). It reads the message of the customer and works in es-419 and pt-BR without Portuguese training data. It needs no tabular signal. We must write its data for the project.
2. **An escalation predictor** (`was_escalated`) on fields known when a call starts. Single fields are flat (spread 0.65% to 1.59%). Nobody fitted a combined model. The target is on calls, not on complaints, and the two are not linked.
3. **A classical classifier on tabular columns or on `description`.** Ruled out: the columns have no signal, and `description` leaks the label.

## Decision

**Option 1.** A prompted LLM classifies the dispute category from the message of the customer. We compare it on the same held-out cases with a keyword baseline and with the same LLM zero-shot.

- **Data:** customer messages in es-419 and pt-BR, written for the project and declared as simulation. Reference labels come from the design of each case, and a reviewer checks a sample. They do not come from `complaints.category`.
- **Metrics:** accuracy and F1 per class, per locale, plus cost and latency per case ([metrics](../metrics.md#4-learned-component)).

## Consequences

- The evaluation set must exist before the held-out measurement, with a reviewer for Portuguese (decision 15). The results are simulation. We never present them as production performance.
- The measured cost and latency of the LLM go into the operating-efficiency metrics.
- *Updated 9/29:* in the architecture, the classifier runs in Decide, only after policy establishes that a dispute applies. Its output fills the `category` field of `open_dispute`. It never decides eligibility ([System Architecture](../../architecture/system-architecture.md#learned-component)). The label set (all claim subcategories, or only those about charges) waits for a new evidence run that measures the category list.
- The escalation predictor stays a possible extension. It returns only if a combined model beats a rule baseline on a time split.
- *Updated 10/2:* the served app runs the prompted router of [016](016-router-models.md#served-configuration-added-2026-10-02), with the keyword baseline as a fallback for each turn. The router labels the **intent** (charge, missing, out of scope, person), not the dispute category. The model still never decides eligibility and never opens a dispute. A keyword rule fills the category ([ML](../areas/ml.md)).
- *Updated 10/4:* the fraud label cannot replace team-written cases. In this dataset, `is_fraud` has no structure, and a `fraud_score` above 30 is always fraud ([`customer-360/dev-signals-v1`](../../../evidence/customer-360/dev-signals-v1/README.md)).
- *Updated 10/4:* the router also reads a subtype, slots and an optional reply draft. A validator checks each draft, and code fills the facts. The model still never decides ([024](024-model-wording.md)).
