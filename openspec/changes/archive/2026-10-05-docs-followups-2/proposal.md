---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Proposal

## Why

`docs-followups` cleans the documents before the code freeze. Several pages can only be right after the freeze, the final measurement, the redeploy and the release. Examples: the page on what the public link runs, the metrics report with the final numbers, the status of each requirement, the evidence index and the state of the plans in `openspec/changes/` and `team/`.

One final pass, after `release`, makes the whole repository match the build that the evaluators open. It changes only documents. It cites REQ-0013, REQ-0030, REQ-0034 and REQ-0051.

## What Changes

- **Public link pages.** Update `docs/rationale/public-link.md`, the consequences of decision 019, `what-is-real.md` and `mocks.md` with the served model, prompt version, `bundle_hash`, the state of the share and the login rule of `judge-access`.
- **Numbers.** Check that the README, the metrics report and the site cite fields of `summary.json`, and that the final runs are in the evidence index with status and data type.
- **Requirements.** Change a status only where the evidence now exists. Update the dependency chains in `requirements.md`, which we write by hand.
- **Plans.** Archive the finished plans in `openspec/changes/` and sync their specs. Archive this change last.
- **Team.** Update `team/tasks.md`, the schedule and decisions in `team/plan.md`, and close the rows of `team/pending-decisions.md`.
- **Full review of `docs/` and `team/`.** Review all 85 pages for one set of terms, the same status words, the same locale tags and simplified technical English. A script prints the findings. The pass rewrites the pages that need it, with their headings and anchors unchanged, and keeps the official data dictionary as it is.
- **Repository hygiene.** Scan the tracked files for secrets, bucket names, dataset rows and passwords, and check every link.
- **Pitch and presentation.** Before the video: bring the six slides, the video script, the product page and the README pitch to the final numbers and links, and prove each claim. After the tags and the video: regenerate the site numbers, add the release tag, the release link and the video link, and check the public site.
- **Submission.** Compare the delivery checklist with the real repository, link, slides, video and email.

## Capabilities

### New Capabilities
- `final-docs-pass`: the repository documents match the submitted build.

### Modified Capabilities
(none)

## Impact

- `docs/`, `README.md`, `team/`, `openspec/`, `evidence/README.md` and `AGENTS.md`. No application code.

## Non-goals

- Any change to code, prompts, policy, cut-offs, deploy settings or the `bundle_hash`.
- New measurements. A fix that needs code reopens gate G3.
- Changing the content of the official data dictionary, or deleting a page without the owner.
- Pushing, opening a pull request, tags or releases. The owner does them.
