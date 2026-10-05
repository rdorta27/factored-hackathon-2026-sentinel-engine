---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 021 · Dispute policy sources: documented, not adopted

**Date:** 2026-10-02
**Status:** Proposed
**Participants:** Rubén (owner)

Replaces nothing yet: [003](003-disputes-flow.md) keeps the 90-day window until a person verifies the sources below.

## Context

The dispute policy in `sentinel-ai-core/config/policy/{mx,co,ar}.yaml` is synthetic ([policy sources](../../rationale/policy-sources.md)). Decision 003 set a 90-day window as "Natalia's assumption, source still to confirm", with the same value for the three countries. Task 21 asked us to fill the verification table from official sources (REQ-0033).

A search on 2026-10-02 read what the regulators and the card networks publish. The result in the [verification table](../../rationale/policy-sources.md#verification-table) is not even:

- México: 90 days in secondary sources only. A 48-hour provisional credit and a 45-day ruling, read on the CONDUSEF page.
- Argentina (credit card): 30 days from the receipt of the statement, read in Ley 25.065.
- Colombia: no fixed window found.
- Visa and Mastercard: time limits between banks, from secondary sources. They are not the window of the customer.

The engine counts days from the transaction date. It has no bank obligation. Gold filters the eligible volume on the same 90 days ([sizing](../../sizing-capacity.md#22-eligible-dispute-volume-90-day-window)). So a change of the window also changes the volume that the analysis uses.

## Options

1. **Keep the demonstration policy and document the sources.** No change in code or configuration. The table and its limits are the deliverable. Cheap and safe before the freeze. The policy is still not real.
2. **Load the values that we read:** México 90 and Argentina 30. No person verified the rows. Colombia still has no value. Gold disagrees with the window of Argentina.
3. **Extend the model first:** the window start per country (cut-off, receipt of the statement, charge), the product, and a bank obligation (provisional credit, response time). It matches the sources. It changes the engine, the texts, the tests and Gold, and it competes with router v3 for the same days.

## Decision

Option 1, proposed. The policy stays synthetic and has that label. The table records what the sources say and how much each row is backed. No value goes into a country file until its row has a name in "Verified by".

## Consequences

- **Gain:** the submission can say which real rules exist, where they differ from ours, and what is not verified. It does not show a demo value as a norm.
- **Cost:** the 90-day window is still not an independent source for any country. For Argentina and Colombia it is probably wrong. The engine cannot express what the sources describe.
- **Open, not built:**
  - A person verifies the rows marked `secondary source only` and reads the Argentine article numbers again.
  - Check the data dictionary for a card network field.
  - Search the window and the response time of Colombia in the Circular Básica Jurídica and the consumer-protection law. This search did not reach them.
  - The owner decides if option 3 becomes a requirement and a change. No requirement exists for it: REQ-0033 is Done, and this is new scope.
- **Not changed:** the policy files, the engine, Gold and the 90-day filter.
- **Limits of the search:** a model did a web search and read the pages. Some official pages did not load, and the tool summarized others. The status column of the table tells which is which. It is not legal advice.
