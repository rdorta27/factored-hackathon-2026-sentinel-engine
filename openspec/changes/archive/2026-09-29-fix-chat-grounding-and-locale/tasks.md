# Tasks: fix-chat-grounding-and-locale

## 1. Grounding (unsafe outcome)

- [x] 1.1 Implement transaction resolution (`matched` / `ambiguous` / `none`) comparing stated date, amount, and merchant against the session customer's candidates, with bounded normalization, owner Felix, per `docs/build/conversation.md#when-opening-a-dispute`; verify exact match, multi-match, no-match, and contradictory-detail cases — evidence: `sentinel-login/tests/test_grounding.py`.
- [x] 1.2 Implement the bilingual statement parser (Spanish and Portuguese month names, `cargo`/`cobro`/`cobrança`, and the `1.000,00` and `1,000.00` amount conventions) feeding the same normalizer, owner Felix, per `docs/build/conversation.md#language`; verify Spanish and Portuguese messages about the same charge resolve to the same candidate and that a Portuguese ambiguous message clarifies — evidence: `sentinel-login/tests/test_grounding_locales.py`.
- [x] 1.3 Add the `candidates` list to the `clarification` reply and route every non-matched outcome to it, keeping the five reply kinds intact, owner Felix, per the `chat` spec delta; verify the payload carries date, amount, currency, and merchant per candidate and that no case is created — evidence: `sentinel-login/tests/test_chat.py`.
- [x] 1.4 Make the mock orchestrator emit customer statements rather than transaction references, so the demo exercises the grounding rule, owner Felix, per `docs/build/areas/ai.md`; verify each existing scenario still resolves and the "wrong date" statement now clarifies — evidence: `sentinel-login/tests/test_chat.py`.

## 2. Reference date and window boundaries

- [x] 2.1 Read the reference date from `SENTINEL_REFERENCE_DATE` (default `2026-06-17`) and pass it to the policy, the confirmation payload, and the UI, owner Felix, per `docs/build/decisions/003-disputes-flow.md`; verify the default, an environment override, and the date appearing in the payload — evidence: `sentinel-login/tests/test_reference_date.py`.
- [x] 2.2 Document the variable and why its default is the dataset's last date in `sentinel-login/README.md`, including the run command that overrides it, per REQ-0039; verify the documented command runs as written — evidence: `sentinel-login/README.md`.
- [x] 2.3 Cover the window boundaries at days 89, 90, and 91 against the reference date, replacing clock-dependent assertions, owner Felix, per decision 003; verify each boundary result and the refusal reason text — evidence: `sentinel-login/tests/test_eligibility.py`.

## 3. Currency, locale, and i18n completeness

- [x] 3.1 Add the mx, co, and ar demo customers to the Gold mock with coherent per-country currency and dates, keeping existing mx references stable, owner Felix, per `docs/build/areas/data.md`; verify each customer lists only their own rows in their own currency — evidence: `sentinel-login/tests/test_gold.py`.
- [x] 3.2 Carry the amount's own currency plus a display-format section in the confirmation and clarify that language never changes the value, owner Felix, per REQ-0041; verify the same transaction keeps its currency across languages and only the formatting differs — evidence: `sentinel-login/tests/test_disputes.py`.
- [x] 3.4 Replace every remaining raw key and ISO date in the card and shell with translated strings and locale-formatted values, adding the missing keys to `es-419`, `es-MX`, `es-CO`, `es-AR`, and `pt-BR`, owner Felix, per `docs/build/conversation.md#language`; verify the completeness test fails on a removed key and passes with all five locales — evidence: `sentinel-login/tests/test_i18n.py`.
- [x] 3.5 Add the `no_funds_held` statement and the `display` block (formatted amount, date, currency, reference date) to the confirmation contract, and share the field-level change note from `design.md` with Rubén, owner Felix, per REQ-0041 and REQ-0004; verify the contract tests assert `hold` is gone, `no_funds_held` is present, and extras are still rejected — evidence: `sentinel-login/tests/test_chat_contract.py`.

## 4. Hold removal and root redirect

- [x] 4.1 Remove the amount-hold field from the customer-facing payload and receipt, replacing it with the explicit `no_funds_held` statement, owner Felix, per REQ-0004; verify no text claims a hold and the contract test asserts its absence — evidence: `sentinel-login/tests/test_disputes.py`.
- [x] 4.2 Redirect `/` to `/ui/` and verify the redirect alongside the API routes, owner Felix, per `docs/build/decisions/006-frontend.md`; verify the redirect status and that every API path still answers — evidence: `sentinel-login/tests/test_i18n.py`.

## 5. Functional interface additions (no restyling)

- [x] 5.1 Add the transactions panel that lists the customer's charges and starts that exact dispute on tap, owner Felix, per `docs/build/decisions/006-frontend.md`; verify in the browser that tapping a charge opens that transaction and that the panel stays inside the session customer — evidence: `sentinel-login/app/ui/static/app.js`.
- [x] 5.2 Render clarification candidates as quick-reply chips and add typing and loading states for in-flight requests, keeping the existing minimal styles, owner Felix, per REQ-0042; verify a chip continues the conversation with the explicit choice — evidence: `sentinel-login/app/ui/static/app.js`.
- [x] 5.3 Show the effective reference date on screen and in the receipt, and state in text that no funds were held, owner Felix, per REQ-0039 and REQ-0004; verify the rendered line matches `SENTINEL_REFERENCE_DATE` — evidence: `sentinel-login/app/ui/static/app.js`.

## 6. Verification

- [x] 6.1 Record the regression walkthrough (the reported case with the wrong date, Spanish and Portuguese grounding, days 89/90/91, per-country currency, locale switch keeping values, no-hold statement, root redirect) across `/ui/` and `/docs`, owner Felix, per `docs/build/security.md`; verify every row reproduces the reported bug as fixed and that the full suite passes — evidence: `openspec/changes/fix-chat-grounding-and-locale/regression-checks.md`.
