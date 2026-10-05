---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Proposal

## Why

A judge opens the public link with no guide. The chat page shows "Quick test" buttons that send a ready phrase, and cards named "test case". A judge can read these as a scripted demo or as unit tests. Nothing on the page says which parts are simulated, which model answers or which build runs. The brief asks the team to label mocks, and the evaluators weigh a working demo first.

This change makes the page explain itself. It adds text and read-only elements. It does not change the chat flow, the policy, the prompt or the API. It cites REQ-0038, REQ-0031 and REQ-0032.

## What Changes

- **Clear label.** "Quick test" becomes "Try an example" (and its es-419 and pt-BR text). The i18n key `demoHint` stays.
- **Demo only.** The example buttons and their label show only when the demo is available (`demoAvailable`, the condition of the demo banner). A bank deployment does not show them.
- **Build line.** A footer line reads `GET /api/v1/health` and shows the model, the prompt version, a short `bundle_hash` and `gold_source`. It links the page to the measured build.
- **Guide for the judge.** A collapsible panel on the entry page lists the three cases to try, what to look for, and what is simulated (Gold data, test login, demo advisor, synthetic policy).
- **Checks.** Existing tests, the phone captures at 390 px and `scripts/e2e_check.py` pass after the change.

## Capabilities

### New Capabilities
- `demo-interface`: the page labels what is simulated, which build runs and how to try each case.

### Modified Capabilities
(none)

## Impact

- `sentinel-ai-core/app/static/` (`index.html`, `app.js`, `styles.css`, `i18n/es-419.json`, `i18n/pt-BR.json`), the UI tests, the screenshots of `docs/` and the requirement card of REQ-0038.

## Non-goals

- Any change to the chat flow, the policy, the prompt, the cut-offs or the API payloads.
- Renaming an element id, a `data-testid` or an i18n key.
- A reset button or any control that writes state.
- New flows or new languages.
