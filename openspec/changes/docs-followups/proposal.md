---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

Several documents drifted while the code moved. A check of `origin/main` on 2026-10-04 found:

- The report of the manual test of Felix marks point 6 and point 10 as passed. Point 10 (the phone layout) belongs to `bank-ui`, and point 6 (a direct "why" question) belongs to `chat-start`.
- The spec of `flow-fixes` has no scenario for the change in `app/policy/engine.py`.
- 59 citations in `openspec/specs/` still say "Pending" for requirements that are now done.
- Three finished plans (`flow-fixes`, `router-v3`, `bank-ui`) are still in `openspec/changes/`.
- 38 pages in `docs/` and `team/` are not yet in simplified technical English.
- Seven remote branches are merged and no longer needed.
- The `sentinel-login/` folder is a reference page that nothing serves. Eight files still name it.
- The `docs/understand/` folder mixes four kinds of page: the challenge overview, the dataset, the glossary and the official data dictionary. The name hides what each page holds. 23 files link to it.

Evaluators read these pages first. A wrong "passed" or an old status costs trust, and the brief gives weight to honest limits.

## What Changes

- **Report of Felix.** Point 10 becomes "passed (bank-ui)" only if the phone screenshots at 390 px prove it. Point 6 becomes "partial" until `chat-start` is merged, then "passed".
- **Spec.** Add the missing scenario to `flow-fixes`: after two requests for an advisor, a request about another charge continues the normal flow.
- **Citations.** A script lists each cited status that differs from `docs/requirements/requirements.md`, and the fix updates them.
- **Archive.** Archive the three finished plans when the owner asks, so the main specs include their rules.
- **Plain English.** Rewrite the five requirement files, `metrics.md`, `sizing-capacity.md`, `security.md`, `conversation.md` and `data_inventory.md` in ASD-STE100. The other pages stay out of scope.
- **Evidence index.** Add each new run to `evidence/README.md` as it lands, with its status and data type.
- **Branch list.** List the merged remote branches. The owner deletes them.
- **Cleanup.** Remove `sentinel-login/`, rewrite the references to it, record the removal in decision 009, and add a link check to the CI workflow.
- **Move `docs/understand/`.** Move its pages to `docs/overview.md`, `docs/data/` and `docs/glossary/`, fix the links, update `AGENTS.md` and `team/`, and remove the folder. The pages keep their content and anchors.

## Capabilities

### New Capabilities
- `evidence-index`: the rule that every frozen run is listed with its status and data type.
- `repo-cleanup`: no unused reference app and no dead link.

### Modified Capabilities
(none)

## Impact

- `team/` (tests report, plan, tasks and pending decisions), `AGENTS.md`, `openspec/specs/` and `openspec/changes/`, `docs/requirements/`, `docs/build/`, `evidence/README.md`.
- No application code changes. One comment in `sentinel-ai-core/app/schemas/chat.py` changes. `sentinel-login/` is removed.

## Non-goals

- Deleting archived OpenSpec changes that name `sentinel-login`.
- Rewriting all 38 pages. Only the pages that the evaluators read first.
- Deleting remote branches or pushing. The owner does both.
- Rewriting the content of the moved pages. The move changes paths and links only.
