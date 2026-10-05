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

This change fixes these defects. Manual tests then found more gaps, and the change covers them: a reload lost the view, the advisor could not read the handoff as data, and one charge could file two tickets. It cites REQ-0038, REQ-0042 and REQ-0008.

## What Changes

- **One turn at a time.** All send controls lock while a turn runs.
- **The right language.** The thread redraws after each locale load, and only the last locale request counts.
- **No stale chips.** The candidate chips of closed turns are disabled.
- **Faster steps.** The step staging is skipped when the panel is hidden, and its pause is 500 ms.
- **Reading and focus.** The page scrolls to the newest message and focuses the input after a turn.
- **Clearer text.** The input has a placeholder and an `aria-label`. The reason of a disabled charge shows as text. Raw i18n keys stay hidden until the first locale loads. Old login errors clear.
- **Advisor view.** It shows country and language names, and it fetches the ticket and the trace in parallel.
- **Navigation.** The view lives in the URL hash. A reload keeps it, the Back button works and an advisor can share the link of a case.
- **Advisor view.** The list and the case sit side by side. The case has the tabs summary, trace and JSON. The JSON has copy and download, and it has no `customer_id`.
- **One ticket for each charge.** The server reuses the ticket of a charge across sessions. A charge with an advisor is not eligible.
- **Closed charges explain themselves.** A tap on a closed charge or a claim opens an information card with the state, the reason and the verified facts.
- **Entry and handoff.** The password form stays visible and has a show button. A handoff says what it did before its card. The session line names the demo persona or the user.
- **Tests and checks.** A test covers each behavior. The suites, the phone check and `scripts/e2e_check.py` pass after the merge with `origin/main`.

## Capabilities

### New Capabilities
- `chat-page-behavior`: how the chat page behaves while a turn runs and when the language changes.

### Modified Capabilities
(none)

## Impact

- `sentinel-ai-core/app/static/` (`app.js`, `index.html`, `styles.css`, the i18n files), the page tests, REQ-0038 and `team/tasks.md`.
- Backend: `app/routers/demo_chat.py` (reuse a ticket), `app/routers/demo_transactions.py` and `app/schemas/chat.py` (three new fields on a closed charge). `bundle_hash` does not change.

## Non-goals

- A change to the router, the policy, the prompt or the cut-offs. The API only gains three optional fields on a charge.
- Confirm the charge before a handoff when the customer names it in free text. This changes the measured flow and needs its own change.
- A change to an element id, a `data-testid` or an i18n key.
- A new account panel. The demo data holds one masked product for each customer, and nothing more.
