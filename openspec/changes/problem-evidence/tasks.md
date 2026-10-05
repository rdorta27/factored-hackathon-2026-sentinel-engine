---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [analysis](../../../docs/build/areas/analysis.md). Decisions: [003](../../../docs/build/decisions/003-disputes-flow.md), [008](../../../docs/build/decisions/008-account-inquiry-scope.md). Paths are relative to the repository root. Raw data stays in `sentinel-data-engine/data/raw/` (not in git).

## 1. The run

- [x] 1.1 Read the dictionary and the call table. Write the mapping from reasons for the call to candidate workflows as a table in the README of the run, and commit it before any number. Evidence: `evidence/problem/dev-v1/README.md`.
- [x] 1.2 Write `evidence/problem/dev-v1/measure_problem.py` with modes `reasons`, `demand`, `hours`, `missing`, `summary` and `verify`. Evidence: the script and a test of the helper functions on a small fixture.
- [x] 1.3 Run it on the development zone and freeze `summary.json` and `MANIFEST.md`. Evidence: `verify` prints OK on every line, and two runs of `summary` give the same file.

## 2. The documents

- [x] 2.1 Write `docs/rationale/problem-and-demand.md` in plain English: the problem, the demand, the hours, and what the data cannot say. Each number cites a field of `summary.json`. Evidence: the page.
- [ ] 2.2 Replace the projected busy-day figures in `docs/sizing_capacity.md` with the measured ones, and say which are still projections. Evidence: the page.
- [ ] 2.3 Update the evidence of REQ-0014 and REQ-0053, add the run to `evidence/README.md`, and add a pointer in `docs/build/flows/03-flow-selection.md`. Evidence: those files.
- [ ] 2.4 List the fields that feed the slide "why" in the plan of `pitch-site`. Evidence: `.local/final-push/plans/pitch-site.md` (the owner copies it).
