---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 008 · Account-inquiry scope

**Date:** 2026-09-29
**Status:** Accepted
**Participants:** Rubén

## Context

The disputes flow starts as an account inquiry ([decision 003](003-disputes-flow.md), [flow selection](../flows/03-flow-selection.md#suggested-flow)). The reason: the demand is in transactional calls (35% of calls), not in dispute claims. In the data, an account inquiry covers balances, movements, and declined, pending or reversed payments.

The architecture has one read tool, `lookup_transactions`. It returns charges and their status, but no balances and no product data. The brief asks for one coherent workflow and gives no extra points for more workflows.

Requirements: REQ-0002 (clarify or abstain), REQ-0003 (verified records only), REQ-0043 (check the status before a dispute).

## Options

1. **Limit the entry to charges and transactions.**
   - For: one read tool, one data contract, one coherent workflow. Code can verify every answer against Gold.
   - Against: the system does not serve part of the transactional demand (balances, product questions).
2. **Add a `lookup_products` tool for balances and product details.**
   - For: it covers more of the inquiry demand.
   - Against: a second data contract, more policy and failure cases, and a second workflow that the brief does not reward. The product snapshot is biased ([dataset](../../data/dataset.md)).

## Decision

**Option 1.** The entry covers what a charge is, its status (Approved, Declined, Pending, Reversed) and whether the customer can dispute it. Balances, products, cards and credit are out of scope. The assistant says so and offers a handoff.

## Consequences

- The [system](../../architecture/specification.md#scope) keeps four tools. Understand classifies each request as charge inquiry, dispute or out of scope.
- Out-of-scope requests exercise the "ambiguous or unsupported" demo case (REQ-0010).
- The demand argument of the flow selection must say that the system serves only the share of transactional calls about charges. The calls cannot measure that share, because the product field is empty on 60% of them.
- A later `lookup_products` is an extension behind a new tool contract, not a redesign.
- *Updated 10/4:* the team measured if products, balances and complaint history could support a charge investigation. They cannot. The balance has no usable as-of date, blocked products have no transactions, and complaints cannot be tied to a charge ([`customer-360/dev-v1`](../../../evidence/customer-360/dev-v1/README.md), [investigation data support](../../rationale/investigation-data-support.md)). This decision does not change.
