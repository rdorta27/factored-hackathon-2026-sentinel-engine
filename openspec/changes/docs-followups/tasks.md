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

- [ ] 3.1 Add each run that exists now (`select-v3d`, `calibration-v3`, the problem run, the charge-ranker runs and `train-v1`) to `evidence/README.md` with its status and data type. Update the sentence on which runs verify offline. The `eval-v8` and robustness runs are added by `post-freeze` (tasks 2.4 and 3.3). Evidence: the file.

## 4. Archive and branches (when the owner asks)

- [ ] 4.1 Archive `flow-fixes`, `router-v3` and `bank-ui` in that order, after tasks 1.2 and 1.3. Evidence: `openspec/changes/archive/` and the synced main specs.
- [ ] 4.2 List the merged remote branches for the owner to delete: `feat/flow-fixes`, `feat/router-v3`, `feat/bank-ui`, `feat/ui-product`, `feat/router-confidence`, `feat/evaluation-final` and `evidence/customer-signals`. Evidence: the list in the pull request description.

## 5. Cleanup

- [ ] 5.1 Find every use of `sentinel-login/`: imports, tests, the Dockerfile, the CI workflow and the docs. Confirm that nothing serves or tests it ([009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md)). Evidence: the `grep` output in the commit body.
- [ ] 5.2 Remove the folder with `git rm -r sentinel-login`. Add a short note to decision 009 that the reference page is removed and why. Evidence: the diff and both test suites green.
- [ ] 5.3 Remove or rewrite each reference: `AGENTS.md` (layout table), `README.md`, `docs/architecture/system-architecture.md`, `sentinel-ai-core/README.md`, the comment in `sentinel-ai-core/app/schemas/chat.py`, `team/plan.md`, `team/tasks.md` and `team/pending-decisions.md`. Leave `openspec/changes/archive/` unchanged. Evidence: `grep -rI sentinel-login` finds only the archive.
- [ ] 5.4 Add `scripts/check_links.py`: it checks that each relative link in the Markdown files outside the archive points to a file, and it runs in the CI workflow. Fix the links it finds. Evidence: the script prints no broken link.
