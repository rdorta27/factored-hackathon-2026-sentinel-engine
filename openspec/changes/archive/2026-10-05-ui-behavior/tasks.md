---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [006](../../../docs/build/decisions/006-frontend.md). Paths are under `sentinel-ai-core/app/static/` unless stated. Do not rename an id, a `data-testid` or an i18n key. Never push or open a pull request.

Runs before gate G3. Merge after `live-ops`, because `scripts/e2e_check.py` checks elements of this page.

## 1. Fixes (done in commit 317010b)

- [x] 1.1 Lock all send controls while a turn runs, so a double click sends one turn. Evidence: `app.js`.
- [x] 1.2 Redraw the thread after each locale load and keep only the last locale request, so the welcome of a persona shows in its language. Evidence: `app.js`.
- [x] 1.3 Disable the candidate chips of closed turns. Evidence: `app.js`, `styles.css`.
- [x] 1.4 Skip the step staging when the panel is not visible and cut the pause to 500 ms. Evidence: `app.js`.
- [x] 1.5 Scroll to the newest message and focus the input after a turn. Evidence: `app.js`.
- [x] 1.6 Add a placeholder and an `aria-label` to the chat input. Evidence: `index.html`.
- [x] 1.7 Show the reason of a disabled charge as text. Evidence: `app.js`, `styles.css`.
- [x] 1.8 Hide raw i18n keys until the first locale loads, and clear old login errors. Evidence: `app.js`.
- [x] 1.9 Show country and language names in the advisor view and fetch the ticket and the trace in parallel. Evidence: `app.js`.

## 2. Tests

- [x] 2.1 Test that a double click on "send" sends one turn, and that the controls unlock when the turn fails or times out. Evidence: a test in `sentinel-ai-core/tests/`.
- [x] 2.2 Test that the thread redraws after a locale load, that only the last locale request counts, and that raw keys stay hidden until the first load. Evidence: a test.
- [x] 2.3 Test that the chips of a closed turn are disabled, and that the advisor view shows names. Evidence: a test.

## 3. Merge and checks

- [x] 3.1 Merge `origin/main` into this branch and resolve the conflict in `app.js` by hand. Keep the changes of `demo-clarity` and `judge-access` (the example buttons, the build line, the judge guide, the simulated-data notice and the empty-account messages). Evidence: the merge commit and a note of what was kept. Note: the merge was a fast-forward to `f1ddcd2`; the branch held no divergent `app.js`, so no conflict. Both change sets stay: the example buttons, the build line, the judge guide, the simulated-data notice and the empty-account messages.
- [x] 3.2 Run the full suite, the phone check at 390 px and `scripts/e2e_check.py` against a local app. Evidence: the pass count and the table in the commit body. Result: the suite gives 949 passed, 2 skipped. `scripts/e2e_check.py` gives 8 PASS: the six demo cases, the manual test replay and the phone layout at 390 px (no scroll, form, build line, closed guide).
- [x] 3.3 Show the owner the entry page and the chat at 390 px before the merge. Evidence: the screenshots. Result: the owner approved on 10/05.

## 4. Requirements and team

- [x] 4.1 Update the card of REQ-0038 with the new evidence. Change a status only where the evidence exists. Evidence: `docs/requirements/frontend-backend.md`.
- [x] 4.2 Update `team/tasks.md`. Evidence: the file.
