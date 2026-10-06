---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Plain text, no tools.** A hand-written `CHANGELOG.md` in the "Keep a Changelog" shape. No release tool, so there is nothing to install.
2. **Two tags only.** `v0.9-demo` marks the last state with all demo code merged. `v1.0-submission` marks the delivered state. More tags would add noise.
3. **The commit hook rejects version numbers in messages.** Tags are not commit messages, so they are allowed. The changelog uses dates and the tag names.
4. **Contributing page for humans.** `AGENTS.md` stays the source for agents. `CONTRIBUTING.md` is short and links to it.
5. **The checklist is a table with owners.** Each row has one owner and one proof, such as a link or a command output.
6. **Written in two parts.** The changelog, the guide, the checklist and the freeze procedure are written now. The last changelog entries, the release notes and the tag commands need the final numbers, so `post-freeze` writes them. `docs-followups-2` makes the last pass.
7. **The freeze procedure comes first.** Gate G3 (`post-freeze` task 1.1) reads it. It names `scripts/e2e_check.py` and its `--access-check` mode.

## Risks / Trade-offs

- **Tags need a push.** The tasks stop at the commands. The owner runs them.
- **The changelog can drift.** The entry for each pull request is a small task in that pull request's checklist.
