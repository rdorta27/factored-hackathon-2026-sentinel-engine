# 010 · Suspected-fraud handoff rule

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner), team review pending

Closes pending decision 25. Rationale for the presentation: [policy thresholds](../../rationale/policy-thresholds.md). OpenSpec change: `add-fraud-and-high-amount-rules`.

## Context

The policy engine had a suspected-fraud rule that never fired: the threshold was null, the fraud score never reached the candidate, and nothing reported the customer's "it was not me" claim. The brief asks the system to know when not to act and to keep policy outside model prose (REQ-0006, REQ-0007, REQ-0033). The dataset ships no bank policy, and currency belongs to the product, not the country ([dataset assumptions](../../understand/dataset.md#assumptions)).

## Options

1. **Claim only:** escalate when the customer says the charge was not theirs. Simple; misses charges the data flags as risky.
2. **Score only:** escalate above a `fraud_score` threshold. Uses the data; ignores what the customer says.
3. **Both, with separate rule ids (`fraud.claim`, `fraud.score`).** Covers both signals; the advisor and the logs show which one escalated (REQ-0029).

`is_fraud` is excluded in every option: it is known only after an investigation.

## Decision

Option 3. The score threshold is the p95 of the development window (2024Q4) per account country and charge currency, from groups of at least 100 charges, read from `evidence/evaluation/2024Q4-v2/summary.json` (`account_thresholds.groups.<country>.<currency>.fraud_score.p95`) into `sentinel-ai-core/config/policy/{mx,co,ar}.yaml`. A currency without data has no value and the score rule does not fire for it (Mexican MXN). The claim is detected from explicit wording ("no fui yo", "não fui eu"); "no reconozco este cargo" is the normal dispute intent and is not a claim. The fraud score never goes to the model ([what the model never receives](../../rationale/model-data-minimization.md)).

## Consequences

- About 5% of charges per group go to an advisor: a workload choice, not a measure of fraud-detection precision.
- The values are synthetic (`synthetic: true`); a bank replaces them in the country file without code changes, and each decision records the policy file version.
- The customer never sees the word fraud or the score; the reply uses the review handoff text.
- Claim recall depends on keywords and is measured by evaluation cases (`2024Q4-eval-v6`), not assumed.
