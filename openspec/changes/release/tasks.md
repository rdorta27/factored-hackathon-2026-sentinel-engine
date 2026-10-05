---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [analysis](../../../docs/build/areas/analysis.md). Decisions: [002](../../../docs/build/decisions/002-openspec.md). Paths are relative to the repository root. No code changes.

**Mode.** Every task is automatic. No task waits for the owner or for another plan. A row of the checklist that has no proof yet is marked pending, and `docs-followups-2` and the `video` change fill it. No task creates a tag.

**Priority (the submission is due on 2026-10-05, 11:59 PM COT).** None of these tasks blocks the submission. Task 3.2 (the freeze procedure) is the only one that `post-freeze` reads. If time runs out, write 3.2 and 3.1 first, and cut 1.1 and 1.2.

## 1. Practice (can start now)

- [x] 1.1 Write `CHANGELOG.md` with one entry per merged pull request (from #42 to the last one) and the milestones. Evidence: the file.
- [x] 1.2 Write `CONTRIBUTING.md`: branches, small pull requests, commit rules, the plan flow, the evidence rules. Evidence: the file. The owner asked for no README link, so the README keeps its "For agents" pointer only.

## 2. Tags and release notes

The release notes and the tag commands need the final numbers. They moved to `post-freeze` (task 5.3).


## 3. Submission

- [x] 3.1 Write the submission checklist in `docs/build/delivery.md`: repository name, deployed link, site link, slides PDF, video, email address, the credentials block of the email (use the template of `judge-access` 3.3, never a real password), Pages setting, secret scan, green test run. Each row has an owner and a proof. Evidence: the table.
- [x] 3.2 Write the freeze procedure (it must exist before gate G3, `post-freeze` task 1.1): what must be merged, the order of the last checks and the rule of no change after the last check. Evidence: the section.

## Moved to `post-freeze`

The last README review and the last changelog entries (old 4.1) now live in the `post-freeze` change, with the release notes and the tag commands (old 2.1, now `post-freeze` 5.3). This plan closes when the changelog, the guide, the release notes, the checklist and the freeze procedure are merged.
