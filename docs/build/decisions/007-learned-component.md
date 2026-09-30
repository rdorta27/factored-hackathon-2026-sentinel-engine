# 007 · Learned component: prompted LLM classifier

**Date:** 2026-09-29
**Status:** Accepted
**Participants:** Team

## Context

The brief requires at least one learned component compared with a baseline on the same held-out data, with valid labels and no leakage (REQ-0016, REQ-0017). The [flow selection](../flows/03-flow-selection.md) found no single field that separates any of the four flows' targets, a label leak in the complaints (`description` contains `category` in every row), and transcripts that are templates. Only approved data may be used, and team-written data must be labeled as such (REQ-0031).

## Options

1. **Prompted LLM that classifies the dispute category** (few-shot examples from the development split only). Reads the customer's message, works in es-419 and pt-BR without Portuguese training data, and needs no tabular signal. Its data has to be written for the project.
2. **Escalation predictor** (`was_escalated`) on fields known when a call starts. Single fields are flat (spread 0.65% to 1.59%); a combined model was not fitted, and the target lives on calls, not on complaints, which are not linked.
3. **Classical classifier on tabular columns or on `description`.** Ruled out: no signal in the columns, leak in `description`.

## Decision

**Option 1.** A prompted LLM classifies the dispute category from the customer's message, and is compared on the same held-out cases with a keyword baseline and with the same LLM zero-shot.

- **Data:** customer messages in es-419 and pt-BR written for the project, declared as simulation. Reference labels come from the design of each case and are reviewed on a sample; they do not come from `complaints.category`.
- **Metrics:** accuracy and F1 per class, by locale, plus cost and latency per case ([metrics](../metrics.md#4-learned-component)).

## Consequences

- The evaluation set must exist before the held-out measurement, with a reviewer for Portuguese (decision 15). Results are simulation and are never presented as production performance.
- The measured cost and latency of the LLM go into the operating-efficiency metrics.
- *Updated 9/29:* in the architecture the classifier runs in Decide, only after policy has established that a dispute applies; its output fills the `category` field of `open_dispute` and never decides eligibility ([System Architecture](../../architecture/system-architecture.md#learned-component)). The label set (all claim subcategories or only charge-related ones) is pending until the category list is measured in a new evidence run.
- The escalation predictor stays a possible extension; it returns only if a combined model beats a rule baseline on a time split.
