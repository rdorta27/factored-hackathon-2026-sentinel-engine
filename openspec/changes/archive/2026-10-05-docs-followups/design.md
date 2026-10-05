---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Honest first.** A row of the Felix report changes only with proof. The proof for point 10 is the set of phone screenshots at 390 px. The proof for point 6 is a passing direct question in the report of `chat-start`.
2. **Order of work follows the plans.** The archive comes last, because it merges deltas into the main specs. The citation fix comes before the archive, so the archive does not copy old statuses.
3. **Small, separate branches.** Each group of tasks is one commit group, so the owner can open small pull requests (the organizers value this).
4. **Scope of the English pass.** Only the pages that a reader opens first. A header `last_reviewed` marks each page that is done.
5. **A script for the citations.** It reads the status table of `requirements.md` and every `Traces to REQ-… (P#, Status)` in the specs, and prints the differences. The fix changes only the status text.

6. **The move comes last.** Other plans keep adding links to the old paths until they merge. The link check (task 5.4) comes first and proves the move.
7. **Move, do not rewrite.** The pages keep their headings and anchors, so older links with an anchor still work after the path is fixed. `git mv` keeps the history.

## Risks / Trade-offs

- **Broken links from other branches.** A branch that adds a link to `docs/understand/` breaks after the move. The link check finds it. The owner merges the move after the other plans.
- **`AGENTS.md` names the old path.** It is the guide for each agent. Task 6.4 updates it in the same commit group as the move.

- **The archive changes the main specs.** The owner chooses the moment. The tasks say "when asked".
- **Pages in two states.** During the work, some pages have the header and some do not. `AGENTS.md` already says how to list them.
