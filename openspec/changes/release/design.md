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
6. **Written last.** The changelog entries for the last pull requests are added after the freeze. The rest can be written now.

## Risks / Trade-offs

- **Tags need a push.** The tasks stop at the commands. The owner runs them.
- **The changelog can drift.** The entry for each pull request is a small task in that pull request's checklist.
