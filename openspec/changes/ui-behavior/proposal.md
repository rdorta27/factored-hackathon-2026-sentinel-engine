---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Proposal

## Why

Manual tests of the chat page found behavior defects that the evaluators can see in the first minute:

- A double click on "send" sent a second turn. With the real model that is a second call and a second answer.
- The welcome of a demo persona showed in `es-419`, whatever the language of the persona.
- The candidate chips of a closed turn stayed active, so a customer could pick a charge from an old question.
- The thread did not scroll to the newest message, and the input lost the focus after a turn.
- The page showed raw i18n keys until the first locale loaded, and an old login error stayed on screen.
- The advisor view showed language and country codes, and it fetched the ticket and its trace one after the other.

This change fixes these defects in the page only. It cites REQ-0038 and REQ-0042.

## What Changes

- **One turn at a time.** All send controls lock while a turn runs.
- **The right language.** The thread redraws after each locale load, and only the last locale request counts.
- **No stale chips.** The candidate chips of closed turns are disabled.
- **Faster steps.** The step staging is skipped when the panel is hidden, and its pause is 500 ms.
- **Reading and focus.** The page scrolls to the newest message and focuses the input after a turn.
- **Clearer text.** The input has a placeholder and an `aria-label`. The reason of a disabled charge shows as text. Raw i18n keys stay hidden until the first locale loads. Old login errors clear.
- **Advisor view.** It shows country and language names, and it fetches the ticket and the trace in parallel.
- **Tests and checks.** A test covers each behavior. The suites, the phone check and `scripts/e2e_check.py` pass after the merge with `origin/main`.

## Capabilities

### New Capabilities
- `chat-page-behavior`: how the chat page behaves while a turn runs and when the language changes.

### Modified Capabilities
(none)

## Impact

- `sentinel-ai-core/app/static/` (`app.js`, `index.html`, `styles.css`), the page tests, REQ-0038 and `team/tasks.md`.

## Non-goals

- A change to the router, the policy, the prompt, the cut-offs or the API.
- A change to an element id, a `data-testid` or an i18n key.
- New features. This change fixes behavior.
