---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [analysis](../../../docs/build/areas/analysis.md). Paths are relative to the repository root. No code changes.

## 1. Correct what is wrong now

- [x] 1.1 In `team/chat-manual-tests.md`, `bank-ui` and `chat-start` are merged. Change point 10 to "passed (bank-ui)" if the phone screenshots at 390 px prove it, or to "pending (bank-ui)" if they do not. Change point 6 to "passed" only if the direct "why" question passes in the `chat-start` conversation report. Otherwise write "partial (chat-start)". Evidence: the file and the screenshot names.
- [x] 1.2 Add the missing scenario to the `flow-fixes` spec: after two requests for an advisor, a request about another charge continues the normal flow, and a third request for an advisor escalates. Evidence: `openspec validate flow-fixes --strict`.
- [x] 1.3 Write a script that prints each cited status in `openspec/specs/` that differs from `docs/requirements/requirements.md`, and fix the 59 citations. The script (`scripts/check_spec_citations.py`) found 210 citations that differ in status or priority, and `--fix` corrected them all. Evidence: the script prints no difference.

## 2. Plain English

- [x] 2.1 Rewrite the five requirement files in ASD-STE100, with the header. Keep the headings and the `REQ-####` anchors. Evidence: the files and `grep -rl '^style: ASD-STE100'`.
- [x] 2.2 Rewrite `metrics.md`, `sizing-capacity.md`, `security.md`, `conversation.md` and `data_inventory.md` the same way. Evidence: the files.

## 3. Evidence index

- [x] 3.1 Add each run that exists now (`select-v3d`, `calibration-v3`, the problem run, the charge-ranker runs, `train-v1` and the runs of `robustness-evidence`) to `evidence/README.md` with its status and data type. Update the sentence on which runs verify offline. The `eval-v8` and robustness runs are added by `post-freeze` (tasks 2.4 and 3.3). The merge of `origin/main` already listed every run in `evidence/`. This task re-ran `verify` on 2026-10-05 and updated its column and sentence. Evidence: the file.

## 4. Archive and branches (when the owner asks)

- [x] 4.1 Archive the merged plans in this order: `flow-fixes`, `router-v3`, `bank-ui`, `chat-start`, `problem-evidence`, `trained-baseline`, `charge-ranker` and `robustness-evidence`. Do it after tasks 1.2 and 1.3. Evidence: `openspec/changes/archive/` and the synced main specs.
- [x] 4.2 List the merged remote branches for the owner to delete. Build the list with `git branch -r --merged origin/main`, so it includes the plans merged after 2026-10-04. On 2026-10-05 the list has 45 branches. Delete none until the owner asks. Evidence: the list in the pull request description.

## 5. Cleanup

- [x] 5.1 Find every use of `sentinel-login/`: imports, tests, the Dockerfile, the CI workflow and the docs. Confirm that nothing serves or tests it ([009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md)). Evidence: the `grep` output in the commit body.
- [x] 5.2 Remove the folder with `git rm -r sentinel-login`. Add a short note to decision 009 that the reference page is removed and why. Evidence: the diff and both test suites green.
- [x] 5.3 Remove or rewrite each reference: `AGENTS.md` (layout table), `README.md`, `docs/architecture/system-architecture.md`, `sentinel-ai-core/README.md`, the comment in `sentinel-ai-core/app/schemas/chat.py`, `team/plan.md`, `team/tasks.md` and `team/pending-decisions.md`. Leave `openspec/changes/archive/` unchanged. Evidence: `grep -rI sentinel-login` finds only the archive.
- [x] 5.4 Add `scripts/check_links.py`: it checks that each relative link in the Markdown files outside the archive points to a file, and it runs in the CI workflow. Fix the links it finds. Evidence: the script prints no broken link.

## 6. Move the `docs/understand/` folder

Run this group last. Other plans add links to the old paths until they merge. Task 5.4 must be done first, because it finds every broken link.

- [x] 6.1 Confirm the destinations with the owner (see the open row in `team/pending-decisions.md`). The default is: `overview.md` to `docs/overview.md`, `dataset.md` to `docs/data/dataset.md`, `reference/` to `docs/data/reference/`, and `glossary/` to `docs/glossary/`. Evidence: the decision row moved to "Decided".
- [x] 6.2 Move the files with `git mv`. Keep the content, the headings and the anchors. Change only the relative links inside the moved files. Evidence: the rename list in `git status`.
- [x] 6.3 Fix every link to the old paths. The files that name them are `AGENTS.md`, `README.md`, `docs/README.md`, the requirement files, the decisions 008, 010, 011 and 017, the area pages, `docs/build/` pages, `docs/rationale/` pages, `docs/architecture/` pages and `team/tasks.md`. Evidence: `scripts/check_links.py` prints no broken link, and `grep -rI "understand/"` finds only `openspec/changes/archive/`.
- [x] 6.4 Update `AGENTS.md`: the layout table, the glossary path in the language section, and the data dictionary path in the rule on data. Update the sentence about the exception in `docs/README.md`, its reading order and its index, and the rules in the moved `reference/README.md`. Evidence: the diff.
- [x] 6.5 Remove the empty `docs/understand/` folder. Evidence: `ls docs` does not list it.
- [x] 6.6 Update `team/`: the two links in `team/tasks.md`, a row in the decisions table of `team/plan.md`, and the decision in `team/pending-decisions.md`. Evidence: the three files.

## 7. Rename the replay script

Run this group after group 6. It touches `team/chat-manual-tests.md`, which tasks 1.1 and 6.6 also edit.

- [x] 7.1 Rename `scripts/felix_replay.py` to `scripts/manual_test_replay.py` with `git mv`. Change its docstring, its usage examples and the prefix of its temporary folder. Change the start and end markers to `manual-test-replay:start` and `manual-test-replay:end`, and the generated title to `## Manual test replay (automated)`. Evidence: the diff.
- [x] 7.2 Change the same markers, the title and the run line in `team/chat-manual-tests.md`. Change both in the same commit, because the script finds its block by the markers. Evidence: the diff.
- [x] 7.3 Change the name in `scripts/e2e_check.py` (from `live-ops` 1.3; the file is not in this branch yet, so `live-ops` must use the new name when it merges), in the comment of `scripts/sentinel_client.py` and in the evidence lines of `docs/requirements/frontend-backend.md`. Leave `openspec/changes/flow-fixes/` and `openspec/changes/robustness-evidence/` unchanged, because they are history. Evidence: `grep -rI "felix_replay\|felix-replay"` finds only those two plans.
- [x] 7.4 Run the script once against a local service. It must replace the existing block and not add a second one. Evidence: `git diff` of `team/chat-manual-tests.md` shows one block.
