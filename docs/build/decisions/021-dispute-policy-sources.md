# 021 · Dispute policy sources: documented, not adopted

**Date:** 2026-10-02
**Status:** Proposed
**Participants:** Rubén (owner)

Replaces nothing yet: [003](003-disputes-flow.md) keeps the 90-day window until a person verifies the sources below.

## Context

The dispute policy in `sentinel-ai-core/config/policy/{mx,co,ar}.yaml` is synthetic ([policy sources](../../rationale/policy-sources.md)). Decision 003 set a 90-day window as "Natalia's assumption, source still to confirm", the same value for the three countries. Task 21 asked for the verification table to be filled from official sources (REQ-0033).

A search on 2026-10-02 read what the regulators and card networks publish. The result, in the [verification table](../../rationale/policy-sources.md#verification-table), is uneven:

- México: 90 days seen in secondary sources only; 48-hour provisional credit and a 45-day ruling read on the CONDUSEF page.
- Argentina (credit card): 30 days from receiving the statement, read in Ley 25.065.
- Colombia: no fixed window found.
- Visa and Mastercard: time limits between banks, from secondary sources; not the customer's window.

The engine counts days from the transaction date and has no bank obligation. Gold filters the eligible volume on the same 90 days ([sizing](../../sizing_capacity.md#22-eligible-dispute-volume-90-day-window)), so changing the window also changes the volume the analysis rests on.

## Options

1. **Keep the demonstration policy and document the sources:** nothing changes in code or configuration; the table and its limits are the deliverable. Cheap and safe before the freeze; the policy is still not real.
2. **Load the values that were read:** México 90 and Argentina 30. Rows are not verified by a person, Colombia would still have no value, and Gold would disagree with Argentina's window.
3. **Extend the model first:** window start by country (cut-off, statement receipt, charge), product, and a bank obligation (provisional credit, response time). It matches the sources; it touches the engine, texts, tests and Gold, and it competes with router v3 for the same days.

## Decision

Option 1, proposed. The policy stays synthetic and is labelled so; the table is the record of what the sources say and how far each row is backed. No value moves into a country file until its row has a name in "Verified by".

## Consequences

- **Gained:** the submission can say what real rules exist, where they differ from ours, and what is unverified, without presenting a demo value as a norm.
- **Sacrificed:** the 90-day window is still not an independent source for any country, and for Argentina and Colombia it is probably wrong. The engine cannot express what the sources describe.
- **Pending, not built:**
  - a person verifies the rows marked `secondary source only` and re-reads the Argentine article numbers;
  - the data dictionary is checked for a card network field;
  - Colombia's window and response time are searched in the Circular Básica Jurídica and the consumer-protection law, which this search did not reach;
  - the owner decides whether option 3 becomes a requirement and a change. No requirement was created: REQ-0033 is Done and this would be new scope.
- **Not touched:** policy files, engine, Gold and the 90-day filter.
- **Limits of the search:** web search plus page reads by a model; some official pages did not load, and the tool summarised others. The table's status column says which is which. It is not legal advice.
