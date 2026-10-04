# Design

## Context

`app/static/index.html` holds three views (`view-login`, `view-chat`, `view-queue`) and `app.js` renders with `textContent` only, formats amounts and dates with `Intl` per locale, and reads every visible string from `app/static/i18n/*.json`. `styles.css` may not contain colors or fonts (`tests/test_branding.py`); colors and type come from `branding/brand.css` and `branding/chat.css`, which import Google Fonts. Fixture users are `CUST-0001` (MX), `CUST-0002` (CO), `CUST-0003` (AR) and `ADV-0001`. `GET /api/v1/handoffs` and `/{case_id}` serve the advisor (`require_advisor`); `CaseRow` stores no trace id. Turn records carry `trace_id`, step, outcome, latency, model, route, prompt version, cost and policy version, kept in memory and in `turns.jsonl`. The `chat-ui` spec already forbids internal identifiers on screen. See proposal.md for motivation.

## Decisions

1. **Steps from the records, mapped server-side.** After a turn, the chat router reads the turn's records by `trace_id` and maps them to a closed list of step keys; the reply gains an optional `steps` list. Mapping on the server keeps rule ids and model names out of the browser.
2. **Demo sign-in route.** `POST /api/v1/auth/demo/{persona}` exists only when `SENTINEL_DEMO_AUTH=1`; personas map to fixture users and a locale and create the same session as a password login. The ambiguous persona is `CUST-0001` in pt-BR (decision 017: a pt-BR writer holds an MX, CO or AR account).
3. **Trace on the ticket.** The ticket stores the `trace_id` of the escalating turn (SQLite column with a default for old rows); `GET /api/v1/handoffs/{case_id}/trace` reads its records from the recorder or the JSONL file, advisor role only. With `runtime-and-ci` the file survives restarts.
4. **Fonts in `branding/`.** The three families are OFL; ship the woff2 files used and replace the Google import with `@font-face`.
5. **Keep ids, add `data-testid`.** Existing ids stay; new elements get `data-testid`.
6. **Three PRs:** entry (`index.html`, personas, banner, mark, fonts); chat and panel (`steps`, panel, status labels, chips); advisor (trace route, ticket detail).

## Risks / Trade-offs

- **One-click access weakens identity:** only behind the flag, with the banner and a README limitation (an id alone does not prove identity).
- **Steps drift from behaviour:** the mapping is tested per outcome kind against the records.
- **Merge clashes with `chat-loop`:** the panel PR waits for it and renders its new keys.
- **Trace lost on restart** before `runtime-and-ci`: the detail says the trace is unavailable instead of failing.
