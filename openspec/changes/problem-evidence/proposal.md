---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

The brief asks for "a problem supported by data": why the problem matters, how much demand it has, how good the data is, and why the team chose the workflow. The repository has parts of this: the share of calls about transactions, the number of claims about unrecognized charges, and one total for the calls that end at the first contact. Three numbers that the pitch needs are missing:

- How many calls end at the first contact, for each reason for the call.
- How many cases arrive on a busy day. Today this is a projection, not a measurement.
- How many hours of agent time each candidate workflow uses.

Without them, the problem slide rests on a projection and on the size of one table.

## What Changes

- **A frozen run** `evidence/problem/dev-v1/`: a script, `summary.json`, a manifest of data hashes and a README in plain English. It reads the development zone only (before 2025-07-01) and writes totals only.
- **Four measures.** Each one has its count and a 95% range (the range where the true value falls, with 95% confidence):
  1. Calls solved at the first contact, by reason for the call.
  2. Calls per day, by workflow: the average, a busy-day level (95 of 100 days are below it) and the highest day.
  3. Agent hours per month for each candidate workflow (calls times the average handling time), ranked.
  4. How much data is missing in the fields that these measures use.
- **A mapping** from reasons for the call to workflows, written as a table before any number.
- **Documents.** A plain-English page `docs/rationale/problem-and-demand.md`, and updates to the evidence of REQ-0014 and REQ-0053, the sizing page and the evidence index.
- **Slide numbers.** The plan of `pitch-site` lists which fields feed the slide "why".

## Capabilities

### New Capabilities
- `problem-evidence`: the frozen run that supports the choice of the workflow.

### Modified Capabilities
(none)

## Impact

- `evidence/problem/`, `docs/rationale/`, `docs/sizing_capacity.md`, `evidence/README.md`, the evidence of REQ-0014 and REQ-0053. A pointer in `docs/build/flows/03-flow-selection.md`.

## Non-goals

- A model, or a change to the product.
- Data from the held-out zone (2025-07-01 and later).
- Claims about savings. The saving range stays an offline projection (`docs/build/roi.md`).
