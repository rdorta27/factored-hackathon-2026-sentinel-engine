---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

[`router-v3`](../router-v3/proposal.md) builds the candidate: contract v3, prompt v3, the draft validator and the cut-offs. Judging it needs a different kind of work: rules written before the numbers, a sealed set written by isolated authors, one single measurement, and a verdict that decides what the service serves. That work has a different pace and different dependencies. The sealed set can be written, reviewed and sealed before the code freeze. Only the measurement must wait, because the runner refuses to measure a seal twice and the owner will review the chat before the freeze, so the prompt can still change.

## What Changes

- **Amendment of 018** (rules before numbers): new metrics, targets from development numbers of the baseline and `router_v2`, the spend cap, and the gates of `eval-v7` kept.
- **Four sealed blocks** by isolated authors: the intent block (kind, subtype, slots, openers), the multi-turn resolution block over the mock store, an attack block (marked and unmarked prompt injection, unauthorized access, expired session, bad data, tool failure, multilingual ambiguity) and a set of noisy twins. The gate D7 needs the attack block. All blocks are reviewed, back-translated and sealed under a new hash before the measurement.
- **Dress rehearsal** of the whole pipeline on development data: every candidate, the new metrics, the report and the spend cap, with no sealed case.
- **More reports** that the earlier runs lacked: the ceiling of safe resolution (how many cases can resolve at all, and how many did), a seven-item checklist score for each handoff, latency per conversation, and three repeats of the high-risk subset (attacks and cases that must hand off).
- **Top-up block and prompt ablation** before the freeze: more bases for the intents that have fewer than 10, harder cases, and a development run that shows what the examples add.
- **Moved to `post-freeze`:** the single measurement `2024Q4-eval-v8`, the verdict and serving decision, and the final report. They wait for the code freeze.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `sealed-case-set`: a second sealed set with openers, subtypes, slots and multi-turn resolution.
- `evaluation-runner`: the new metrics of v8.

## Impact

- `sentinel-ai-core/eval/` (metrics, runner, report, cases, seal), decision 018 amendment, `evidence/evaluation-runs/2024Q4-eval-v8/`, the metrics report, README, requirements evidence, the evidence index and the CI workflow.

## Non-goals

- Changes to the prompt, the contract or the validator (they belong to `router-v3`).
- A measurement before the code freeze, or a second measurement of the same seal.
- The measurement and the verdict (see `post-freeze`).
