# Tasks

## 1. Test session and demo date

- [x] 1.1 Declare runtime dependencies `fastapi`, `uvicorn`, and `pydantic`, dev dependencies `httpx` and `pytest`, and Python `>=3.12` in `sentinel-ai-core/pyproject.toml`. Decision: [005](../../../docs/build/decisions/005-backend.md). Verify `requires-python` and the named packages are declared — evidence: `sentinel-ai-core/pyproject.toml`.
- [x] 1.2 Add `app/session/` with opaque cookie login, logout, and current-session routes (`POST /session/login`, `POST /session/logout`, `GET /session/me`), generic failure, lockout, and audit without passwords or tokens. Decision: [005](../../../docs/build/decisions/005-backend.md). Verify 200, identical 401s, 422 on a body `customer_id`, expiry, and lockout — evidence: `sentinel-ai-core/tests/test_session.py`.
- [x] 1.3 Read `SENTINEL_REFERENCE_DATE` once at startup (default `2026-06-17`) and inject it as the demo date. Do not read the wall clock for the window. Decision: [003](../../../docs/build/decisions/003-disputes-flow.md). Verify the default and an override — evidence: `sentinel-ai-core/tests/test_session.py`.
- [x] 1.4 Document that `sentinel-ai-core` is the only submission server, that `sentinel-login/` stays as a reference, and how to set `SENTINEL_REFERENCE_DATE`. Area: [AI](../../../docs/build/areas/ai.md). Verify the documented command matches the startup read — evidence: `sentinel-ai-core/README.md`.

## 2. Gold adapter and listing

- [x] 2.1 Bind `customer_id` in an adapter before `step()`. Map a mock `Refunded` status to Reversed. Do not add a customer argument to `lookup_transactions()`. Area: [data](../../../docs/build/areas/data.md). Verify a foreign reference is absent and the as-of mark is the demo date — evidence: `sentinel-ai-core/tests/test_gold_adapter.py`.
- [x] 2.2 Add session-scoped `GET /transactions` with no customer identifier accepted. Area: [data](../../../docs/build/areas/data.md). Verify the list is only the session customer's rows and a customer identifier is rejected — evidence: `sentinel-ai-core/tests/test_transactions.py`.

## 3. Grounding under the loop

- [x] 3.1 Add the `es-419` and `pt-BR` grounding fake in `app/ai/` (`cargo`, `cobro`, and `cobrança` are charges; amounts `1.000,00` and `1,000.00`). Rank with the demo date. Area: [AI](../../../docs/build/areas/ai.md). Verify Spanish and Portuguese match the same charge, and an ambiguous Portuguese message does not select one — evidence: `sentinel-ai-core/tests/test_grounding.py`.
- [x] 3.2 Stop taking the first charge. A match is input to policy. Person and out-of-scope run before grounding. A structured id is selection when no box is pending, and confirmation only when it matches the pending box. Decision: [005](../../../docs/build/decisions/005-backend.md). Verify a Reversed match explains and does not show a box, and a written yes does not open — evidence: `sentinel-ai-core/tests/test_grounding.py`.

## 4. POST /chat

- [ ] 4.1 Accept only `message` and `selected_reference` on `POST /chat`. Identity comes from the session. Return `clarification`, `confirm_box`, `case_confirmation`, `handoff`, `text`, or `error`. Decision: [005](../../../docs/build/decisions/005-backend.md). Verify 401 without a session, 422 on an extra field, and no open on selection — evidence: `sentinel-ai-core/tests/test_chat.py`.
- [ ] 4.2 On the confirmation turn, issue the token only inside the loop. Do not put it in the request or the response. Emit `case_confirmation` only after read-back, with `source=mock`, and no receipt route. Decision: [006](../../../docs/build/decisions/006-frontend.md). Verify the token is absent from JSON and an unverified write is `handoff` with no case number — evidence: `sentinel-ai-core/tests/test_chat.py`.

## 5. Customer page

- [ ] 5.1 Serve the customer chat from `app/static/`: receipt without a download, chips, transaction panel, locales, reference-date line, and `.chat-confirm`. Read `branding/` as-is. A tap or chip posts `selected_reference` and does not open. Decision: [006](../../../docs/build/decisions/006-frontend.md). Verify the confirm box renders and the identifier is not visible text — evidence: `sentinel-ai-core/tests/test_ui.py`.
- [ ] 5.2 Keep the agent control two-step, mask displayed identifiers, and do not store the session in browser storage. Decision: [004](../../../docs/build/decisions/004-pii-lifecycle.md). Verify the first press does not hand off and the second does — evidence: `sentinel-ai-core/tests/test_ui.py`.

## 6. Separate suites

- [ ] 6.1 Run `sentinel-ai-core` tests and `sentinel-login` tests as separate commands. Do not delete `sentinel-login/`. Area: [AI](../../../docs/build/areas/ai.md). Verify both commands pass on their own — evidence: `sentinel-ai-core/tests/` and `sentinel-login/tests/`.
