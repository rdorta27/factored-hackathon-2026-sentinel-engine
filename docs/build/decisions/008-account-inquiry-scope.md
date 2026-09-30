# 008 · Account-inquiry scope

**Date:** 2026-09-29
**Status:** Accepted
**Participants:** Rubén

## Context

The disputes flow enters through an account inquiry ([decision 003](003-disputes-flow.md), [flow selection](../flows/03-flow-selection.md#suggested-flow)), because demand sits in transactional calls (35% of calls) rather than in dispute claims. An account inquiry in the data covers balances, movements, and declined, pending or reversed payments. The architecture has one read tool, `lookup_transactions`, which returns charges and their status but no balances or product data. The brief asks for one coherent workflow and gives no credit for extra workflows. Requirements: REQ-0002 (clarify or abstain), REQ-0003 (verified records only), REQ-0043 (check status before disputing).

## Options

1. **Limit the entry to charges and transactions.** Pros: one read tool, one data contract, one coherent workflow; every answer can be verified against Gold. Cons: part of the transactional demand (balances, product questions) is not served.
2. **Add a `lookup_products` tool for balances and product details.** Pros: covers more of the inquiry demand. Cons: a second data contract, more policy and failure cases, and a second workflow the brief does not reward; the product snapshot is biased ([dataset](../../understand/dataset.md)).

## Decision

**Option 1.** The entry point covers what a charge is, its status (Approved, Declined, Pending, Reversed) and whether it can be disputed. Balances, products, cards and credit are out of scope: the assistant says so and offers a handoff.

## Consequences

- The [system](../../architecture/specification.md#scope) keeps four tools; Understand classifies each request as charge inquiry, dispute or out of scope.
- Out-of-scope requests exercise the "ambiguous or unsupported" demo case (REQ-0010).
- The demand argument in the flow selection must say that only the charge-related share of transactional calls is served; that share is not measurable from calls, because the product field is blank on 60% of them.
- Adding `lookup_products` later is an extension behind a new tool contract, not a redesign.
