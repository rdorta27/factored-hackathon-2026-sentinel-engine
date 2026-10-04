---
language: en
style: ASD-STE100
ste_reviewed: 2026-10-04
---

# 010 · Suspected-fraud handoff rule

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner), team review pending

Closes pending decision 25. Rationale for the presentation: [policy thresholds](../../rationale/policy-thresholds.md). OpenSpec change: `add-fraud-and-high-amount-rules`.

## Context

The policy engine had a suspected-fraud rule that never fired, for three reasons:

- The threshold was null.
- The fraud score never reached the candidate.
- Nothing reported the "it was not me" claim of the customer.

The brief asks the system to know when not to act, and to keep policy outside the model text (REQ-0006, REQ-0007, REQ-0033). The dataset has no bank policy. Currency belongs to the product, not to the country ([dataset assumptions](../../understand/dataset.md#assumptions)).

## Options

1. **Claim only:** hand off when the customer says that the charge is not theirs. Simple. It misses charges that the data flags as risky.
2. **Score only:** hand off above a `fraud_score` threshold. It uses the data. It ignores what the customer says.
3. **Both, with separate rule ids (`fraud.claim`, `fraud.score`).** It covers both signals. The advisor and the logs show which one caused the handoff (REQ-0029).

No option uses `is_fraud`, because a bank knows it only after an investigation.

## Decision

Option 3.

- The score threshold is the p95 of the development window (2024Q4) per account country and charge currency, from groups of at least 100 charges.
- The values come from `evidence/evaluation/2024Q4-v2/summary.json` (`account_thresholds.groups.<country>.<currency>.fraud_score.p95`) and go into `sentinel-ai-core/config/policy/{mx,co,ar}.yaml`.
- A currency without data has no value, and the score rule does not fire for it (Mexican MXN).
- Code detects the claim from explicit words ("no fui yo", "não fui eu"). "No reconozco este cargo" ("I do not recognize this charge") is the normal dispute intent, not a claim.
- The fraud score never goes to the model ([what the model never receives](../../rationale/model-data-minimization.md)).

## Consequences

- About 5% of charges per group go to an advisor. This is a workload choice, not a measure of fraud-detection precision.
- The values are synthetic (`synthetic: true`). A bank replaces them in the country file without a code change. Each decision records the version of the policy file.
- The customer never sees the word "fraud" or the score. The reply uses the review handoff text.
- Keywords decide the recall of the claim. Evaluation cases measure it (`2024Q4-eval-v6`). We do not assume it.
- *Updated 10/4:* a re-derivation on a later development window confirms that the rule sets a workload. Its precision is low and its recall is about one half (`labels.p95_rule` in [`customer-360/dev-signals-v1`](../../../evidence/customer-360/dev-signals-v1/README.md)). In this dataset, a score above 30 is always fraud, which is an artefact of the generator (`labels.synthetic_artefact`). We do not move the threshold to 30, because a real bank score does not have this boundary.
