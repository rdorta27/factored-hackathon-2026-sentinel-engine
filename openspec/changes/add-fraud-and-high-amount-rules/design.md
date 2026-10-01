# Design

## Context

See proposal.md (Why). The engine already evaluates `fraud.score` and `amount.high` in order (country, person insist, fraud, high amount, status, window, already disputed, fields, person ask, allow) and the chat already maps both hits to a handoff. Three inputs are missing: per-currency values, the fraud score on the candidate, and the not-mine claim. Today `CountryPolicy` holds one `currency` and one value per threshold, and `_amount` skips any charge whose currency differs from the file currency.

The dataset's account countries are only México, Colombia and Argentina; currency belongs to the product (data dictionary: `customers.country`, `products.currency`). `transaction_country` is where a purchase happened and includes foreign countries (for example Brazil), so it cannot group account thresholds.

## Goals / Non-Goals

**Goals:**
- Each threshold is read by account country and charge currency, from values measured on the development window.
- Every activated rule is visible in the demo and covered by a test and an evaluation case.

**Non-Goals:**
- Currency conversion or a USD-normalized threshold.
- Learning a fraud model; the score is the dataset's own column.

## Decisions

**1. Per-currency map in the country file.**
```yaml
thresholds:
  fraud_score:
    values: {MXN: 28.5, USD: 28.7}   # from evidence 2024Q4-v2
    source: evidence/evaluation/2024Q4-v2/summary.json
    decision: 25
  high_amount:
    values: {MXN: ..., USD: ...}
    source: evidence/evaluation/2024Q4-v2/summary.json
    decision: 26
```
The file keeps `currency` as the local currency for display texts. The engine looks up `values[candidate.currency]`; a missing key means the rule does not fire. Alternative considered: one USD threshold on `amount_usd`. Rejected: `amount_usd` may be empty, a USD figure is not the amount the customer sees, and it does not cover the fraud score.

**2. p95 of the development window per country and currency, minimum 100 charges per group.** p95 caps the share of charges sent to an advisor near 5% per group, a workload choice we can state; p90 doubles that load and p99 would rarely show in the demo. A group with fewer than 100 charges in the development window gets no value and is reported as a limitation, so a percentile is never taken from a handful of rows. Values are never chosen on held-out data.

**3. New evidence run, not an edit.** `evidence/evaluation/2024Q4-v2/` comes from a new script version that joins transactions to `customers.country`, normalizes `Mexico` to `México`, groups by country and currency, and adds the product currency share and the empty `amount_usd` count. v1 stays as it is.

**4. Not-mine claim as a structured field with its own rule id.** The baseline uses a short keyword list in es-419 and pt-BR; the router prompt asks for the same boolean. It reaches the engine as `states_not_theirs` and hands off citing `fraud.claim`, distinct from `fraud.score`, so the advisor and the logs show whether the customer's words or the charge's score escalated the case (REQ-0029). Wording alone never fires on "no reconozco". The customer reply never mentions fraud or the score; it reuses the review handoff text.

**5. Freeze as soon as this change lands, not tied to decision 10.** New eval cases (one per rule and currency shown, es-419 and pt-BR for the claim) and new evaluation and adversarial runs are frozen when this change is done. Code freezes Friday 10/2; waiting for the live model risks having no threshold evidence. If the live model lands in time, it gets its own later run; runs are write-once, so an extra one costs nothing.

**6. Demo rows: USD only for the Mexican customer.** One MX USD charge above its thresholds shows that a Mexican USD account has its own values. CO and AR stay in local currency unless the v2 evidence shows USD is common there.

**7. Synthetic values the bank replaces without code.** The values are a team-made synthetic policy (`synthetic: true`), justified by method, not by number: lacking a bank policy, p95 of the development data per country and currency, about 5% of charges to an advisor, a workload choice and not fraud precision. A bank sets its own values by editing the country file: per-currency `values`, `source` pointing to its policy reference instead of an evidence run, and `synthetic: false`. Rule ids do not change, so logs and handoffs stay comparable. The value check against evidence applies only when `source` is an evidence run; a bank source is checked for format only. Each decision records the policy file version, so a past case can be traced to the values in force. In production the file goes through approval by the policy owner and stays versioned (path to production, REQ-0052). This rationale is part of the presentation.

## Risks / Trade-offs

- [The fraud score's scale is 0-100 but observed values sit below ~30] → thresholds come from the observed distribution, and the slides say so.
- [A percentile is not fraud precision] → present it as advisor workload; report how many held-out charges each rule sends to a person.
- [Small currency groups (for example USD in AR)] → minimum group size; no value means no rule, declared as a limitation.
- [Keyword recall for the not-mine claim] → measured by eval cases, not assumed.
- [Breaking file format] → loader and all three files change in the same commit; tests cover a missing currency key.

## Migration Plan

Change the loader and the three files together. Rollback is reverting that commit; with no values the engine behaves as today.
