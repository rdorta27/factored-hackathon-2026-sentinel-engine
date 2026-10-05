---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Design

## Decisions

| Topic | Choice | Reason |
|---|---|---|
| Double click | Lock every send control for the whole turn | One click, one turn. The server stays unchanged |
| Language | Redraw the thread after a locale load. Keep only the last locale request | A late answer of an old request must not win |
| Old chips | Disable the chips of closed turns | A pick from an old question opens the wrong confirm box |
| Raw keys | Hide the text until the first locale loads | The visitor never sees `welcome.title` |
| Advisor view | Names for country and language. Parallel fetch | The advisor reads names, not codes |
| Scope | `app/static/`, plus three small backend edits | The measured behavior and the `bundle_hash` stay the same. The edits only dedupe tickets and add facts to a closed charge |
| Navigation | URL hash, no library | The page stays one HTML file ([006](../../../docs/build/decisions/006-frontend.md)). A hash needs no server route |
| Advisor JSON | Show the ticket and the trace without `customer_id` | The screen never shows the id ([009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md)), so the export does not either |
| Closed charge | The server sends the window facts. The page computes no date | The page never re-derives a policy rule |
| One ticket per charge | Look up the case store, not the conversation | The store outlives the session |

## Risks

| Risk | Control |
|---|---|
| The merge with `origin/main` conflicts in `app.js` (the guide, the build line and the example buttons came after this branch) | Resolve by hand. Keep both sets of changes. Run the page tests, the phone check and `scripts/e2e_check.py` |
| A lock that never unlocks | A test: the controls unlock when the turn fails or times out |
| A change to ids breaks `e2e_check.py` | Do not rename an id or a `data-testid` |

## Order

Merge after `live-ops`, because `scripts/e2e_check.py` checks elements of this page. Merge before gate G3, because the page is part of the frozen build.
