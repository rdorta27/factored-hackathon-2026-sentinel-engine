---
language: en
style: ASD-STE100
ste_reviewed: 2026-10-04
---

# 011 · High-amount handoff threshold

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner), team review pending

Closes pending decision 26. Rationale for the presentation: [policy thresholds](../../rationale/policy-thresholds.md). OpenSpec change: `add-fraud-and-high-amount-rules`.

## Context

A high-value dispute has more financial and reputational risk. A person must review it (REQ-0006). The threshold was null.

Currency belongs to the product. Colombian and Argentine customers have local and USD accounts. In the dataset, every Mexican account is in USD ([dataset assumptions](../../understand/dataset.md#assumptions)). One value per country in one currency would skip every charge in the other currency.

## Options

1. **One value per country in the local currency:** it skips USD charges.
2. **One USD value on `amount_usd`:** the customer does not see this amount. It uses fixed synthetic exchange rates. It is empty in about 5% of ARS and COP charges. Silver does not carry the column.
3. **One value per account country and charge currency.**

## Decision

Option 3.

- The value is the p95 of the development window (2024Q4) per account country and charge currency, from groups of at least 100 charges.
- The values come from `evidence/evaluation/2024Q4-v2/summary.json` (`account_thresholds.groups.<country>.<currency>.amount.p95`) and go into `sentinel-ai-core/config/policy/{mx,co,ar}.yaml`.
- An amount equal to the value does not fire.
- Mexican MXN has no value. The dataset has no MXN accounts. The MXN account of the demo is team-generated, and the demo says so.

## Consequences

- About 5% of charges per group go to an advisor. We state this as a workload choice.
- The USD values are almost equal in the three countries: the currency explains the amount, not the country.
- A bank replaces the values in configuration (`source` set to its policy, `synthetic: false`). The rule ids stay the same.
- We asked in the help channel if USD-only Mexican accounts are intentional. The answer does not change the rule.
- *Updated 10/4:* `amount_usd` is empty on every USD row and on about 5% of ARS and COP rows (`labels.amount_usd_fill_by_currency` in [`customer-360/dev-signals-v1`](../../../evidence/customer-360/dev-signals-v1/README.md)). No Mexican product is in MXN (`products.by_country.México.currency` in [`customer-360/dev-v1`](../../../evidence/customer-360/dev-v1/README.md)).
