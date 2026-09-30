# Tasks: refine-mvp-gold-layer-proof-of-work

## 1. Gold seam and disputes service

- [x] 1.1 Implement the Gold read seam (`GoldTransactions` protocol, invented-row mock for `CUST-0001` covering eligible, stale, refunded, already-disputed, and foreign rows, each with as-of mark) with per-customer filtering, owner Felix, per `docs/build/areas/data.md`; verify unknown and cross-customer references read as absent — evidence: `sentinel-login/tests/test_gold.py`.
- [x] 1.2 Implement eligibility as a pure function of row, injected policy (`window_days`, article), and simulated demo date, owner Felix, per `docs/build/decisions/003-disputes-flow.md`; verify each refusal reason and a window boundary case — evidence: `sentinel-login/tests/test_eligibility.py`.
- [x] 1.3 Implement `DisputeService.create` (policy check, case creation, re-read verification, idempotency-key store, Proof-of-Work payload with hold, rule plus article, SLA deadline, receipt reference, queue status) plus `POST /api/v1/disputes/create` and the plain-text receipt endpoint, owner Felix, per `docs/build/decisions/005-backend.md`; verify single creation, duplicate-key replay, each refusal path, and no proof without verification — evidence: `sentinel-login/tests/test_disputes.py`.

## 2. Chat rewire and contract

- [x] 2.1 Rewire `POST /chat` to resolve transactions through the Gold seam and create cases only via the disputes service, keeping the four mock scenarios and reply kinds stable, owner Felix, per `docs/build/areas/ai.md`; verify the full existing chat suite still passes against mock Gold rows — evidence: `sentinel-login/tests/test_chat.py`.
- [x] 2.2 Extend `CaseConfirmation` with the five Proof-of-Work fields (kind unchanged) and update the contract tests, owner Felix, per `docs/build/decisions/005-backend.md`; verify serialization, extras rejected, and old field assertions intact — evidence: `sentinel-login/tests/test_chat_contract.py`.

## 3. Proof-of-Work card

- [x] 3.1 Render the five Proof-of-Work elements in the receipt card (hold line, rule plus article, SLA countdown text, receipt download link, queue status) with masked data and `textContent`-only rendering, owner Felix, per `docs/build/decisions/006-frontend.md`; verify in the browser against the mock backend for the normal scenario — evidence: `sentinel-login/app/ui/static/app.js`.
- [x] 3.2 Extend the i18n dictionaries with the new card strings across `es-419`, regional overrides, and `pt-BR`, owner Felix, per `docs/build/conversation.md`; verify fallback and completeness tests pass — evidence: `sentinel-login/tests/test_i18n.py`.

## 4. Walkthrough and alignment

- [x] 4.1 Record the Proof-of-Work walkthrough (eligible receipt with all five elements, stale/refunded/prior refusals with handoff, duplicate-key replay, receipt download, attack matrix delta) and confirm the golden-rule alignment note, owner Felix, per `docs/build/security.md`; verify every row shows the specified payload and status — evidence: `openspec/changes/refine-mvp-gold-layer-proof-of-work/proof-checks.md`.
