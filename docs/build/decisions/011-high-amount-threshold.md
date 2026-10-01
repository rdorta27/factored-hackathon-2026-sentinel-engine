# 011 · High-amount handoff threshold

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner), team review pending

Closes pending decision 26. Rationale for the presentation: [policy thresholds](../../rationale/policy-thresholds.md). OpenSpec change: `add-fraud-and-high-amount-rules`.

## Context

High-value disputes carry more financial and reputational risk and should be reviewed by a person (REQ-0006). The threshold was null. Currency belongs to the product: Colombian and Argentine customers hold local and USD accounts, and in the dataset every Mexican account is in USD ([dataset assumptions](../../understand/dataset.md#assumptions)). A single value per country in one currency would skip every charge in the other.

## Options

1. **One value per country in the local currency:** skips USD charges.
2. **One USD value on `amount_usd`:** not the amount the customer sees, rests on fixed synthetic exchange rates, empty in about 5% of ARS and COP charges, and Silver does not carry the column.
3. **One value per account country and charge currency.**

## Decision

Option 3. The value is the p95 of the development window (2024Q4) per account country and charge currency, from groups of at least 100 charges, read from `evidence/evaluation/2024Q4-v2/summary.json` (`account_thresholds.groups.<country>.<currency>.amount.p95`) into `sentinel-ai-core/config/policy/{mx,co,ar}.yaml`. An amount equal to the value does not fire. Mexican MXN has no value: the dataset holds no MXN accounts, and the demo's MXN account is invented and stated as such.

## Consequences

- About 5% of charges per group go to an advisor, stated as a workload choice.
- The USD values come out almost equal across the three countries: the currency, not the country, explains the amount.
- A bank replaces the values in configuration (`source` pointing to its policy, `synthetic: false`); rule ids stay the same.
- Asked in the help channel whether Mexican accounts being USD only is intentional; the answer does not change the rule.
