# Tasks: add-chat-roles-trust-ui

## 1. Customer plus chat plus contract

- [x] 1.1 Add `role` to the session and mock users for `customer`, `advisor`, `admin` with documented demo credentials, owner Felix, per `docs/build/security.md`; verify all 26 existing login tests still pass plus a role-carrying login test — evidence: `sentinel-login/tests/test_roles_login.py`.
- [x] 1.2 Implement the response contract module (`text`, `clarification`, `case_confirmation`, `handoff`, `error`) with strict Pydantic v2 models, owner Felix, per `docs/build/decisions/005-backend.md`; verify each variant serializes and rejects extras — evidence: `sentinel-login/tests/test_chat_contract.py`.
- [x] 1.3 Implement `POST /chat` with `require_session`, message-only body, `Orchestrator`/`CaseStore` protocols, verify-before-claim with bounded retries then handoff, and the 4-scenario mock orchestrator, owner Felix, per `docs/build/areas/ai.md`; verify contract per scenario, 401 without session, 422 on extra fields, and no `case_confirmation` without re-read — evidence: `sentinel-login/tests/test_chat.py`.

## 2. Advisor queue

- [x] 2.1 Implement `require_role`, advisor queue endpoints (list, claim, state change) returning summary projections only, with 403 plus audit on role failure, owner Felix, per `docs/build/security.md`; verify privilege-escalation matrix (customer→advisor 403, advisor→admin 403) and that mock handoffs appear in the queue — evidence: `sentinel-login/tests/test_roles_queue.py`.

## 3. Admin panel

- [x] 3.1 Implement read-only admin endpoints (audit log, counts of logins/failures/lockouts/handoffs/denials, no message text), owner Felix, per `docs/build/areas/analysis.md`; verify counts equal audit events and no conversation content leaks — evidence: `sentinel-login/tests/test_admin.py`.

## 4. Frontend, themes, languages

- [x] 4.1 Implement the vanilla frontend (login, role landing, chat with receipt card and timeline, agent button, masking, `textContent`-only rendering, 401/403 handling) served by the same process, owner Felix, per `docs/build/decisions/006-frontend.md`; verify by loading each role view in the browser against the mock backend — evidence: `sentinel-login/app/ui/`.
- [x] 4.2 Implement themes (CSS variables, OS default, toggle, theme-only localStorage) and i18n (`es-419` base, regional overrides, `pt-BR`, fallback, selector), owner Felix, per `docs/build/conversation.md`; verify fallback (`es-AR` miss → `es-419`), `pt-BR` rendering, and no session data in browser storage — evidence: `sentinel-login/app/ui/i18n/` plus `sentinel-login/tests/test_i18n.py`.

## 5. Trust walkthrough

- [x] 5.1 Record the end-to-end trust walkthrough (normal receipt, ambiguous clarification, high-risk handoff visible in queue, failed-verification handoff, attack matrix extension) in the browser and `/docs`, owner Felix, per `docs/build/security.md`; verify every row shows the specified variant and status — evidence: `openspec/changes/add-chat-roles-trust-ui/trust-checks.md`.
