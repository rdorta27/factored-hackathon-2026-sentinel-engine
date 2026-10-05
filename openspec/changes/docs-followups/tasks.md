---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [analysis](../../../docs/build/areas/analysis.md). Paths are relative to the repository root. No code changes.

## 1. Correct what is wrong now

- [ ] 1.1 In `team/chat-manual-tests.md`, change point 10 to "passed (bank-ui)" if the phone screenshots at 390 px prove it, or to "pending (bank-ui)" if they do not. Change point 6 to "partial (chat-start)". Evidence: the file and the screenshot names.
- [ ] 1.2 Add the missing scenario to the `flow-fixes` spec: after two requests for an advisor, a request about another charge continues the normal flow, and a third request for an advisor escalates. Evidence: `openspec validate flow-fixes --strict`.
- [ ] 1.3 Write a script that prints each cited status in `openspec/specs/` that differs from `docs/requirements/requirements.md`, and fix the 59 citations. Evidence: the script prints no difference.

## 2. Plain English

- [ ] 2.1 Rewrite the five requirement files in ASD-STE100, with the header. Keep the headings and the `REQ-####` anchors. Evidence: the files and `grep -rl '^style: ASD-STE100'`.
- [ ] 2.2 Rewrite `metrics.md`, `sizing_capacity.md`, `security.md`, `conversation.md` and `data_inventory.md` the same way. Evidence: the files.

## 3. Evidence index

- [ ] 3.1 Add each run that lands (`select-v3d`, `calibration-v3`, the problem run, the charge-ranker runs, `train-v1`, the robustness runs, `eval-v8`) to `evidence/README.md` with its status and data type. Update the sentence on which runs verify offline. Evidence: the file.

## 4. Archive and branches (when the owner asks)

- [ ] 4.1 Archive `flow-fixes`, `router-v3` and `bank-ui` in that order, after tasks 1.2 and 1.3. Evidence: `openspec/changes/archive/` and the synced main specs.
- [ ] 4.2 List the merged remote branches for the owner to delete: `feat/flow-fixes`, `feat/router-v3`, `feat/bank-ui`, `feat/ui-product`, `feat/router-confidence`, `feat/evaluation-final` and `evidence/customer-signals`. Evidence: the list in the pull request description.
