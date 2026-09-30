# Trust walkthrough: add-chat-roles-trust-ui

Verified 2026-09-29 with `pytest -q` (60 passed) on Python 3.12.10, plus
browser and `/docs` walkthrough against one `uvicorn` process. Extends the
`sentinel-login` attack matrix (`attack-checks.md`).

## Chat variants (`POST /chat`, role customer)

| Scenario | Request | Expected | Observed | Test |
|---|---|---|---|---|
| Normal dispute | `I dispute the charge of 1000 at ACME` | `case_confirmation`, `verified=true`, id `CASE-0001`, MXN facts, `verified_at`, `source=mock` | as specified | `test_chat.py::test_normal_case_returns_verified_confirmation` |
| Ambiguous | `help with charge` | `clarification`, `missing=transaction` | as specified | `test_ambiguous_message_returns_clarification` |
| High risk | `my card was stolen, fraud!` | `handoff`, `reference=HO-CASE-*`, advisor summary | as specified | `test_high_risk_message_returns_handoff` |
| Broken store | `broken dispute flow error test` | `handoff`, never `case_confirmation` | as specified | `test_broken_store_returns_handoff_never_confirmation` |
| Agent insistence | `I want a human agent` twice | `text` offer, then `handoff` | as specified | `test_agent_request_escalates_on_insistence` |
| Agent button | click | immediate `handoff` (message `Please escalate now to an agent`) | as specified | manual |
| No session | no cookie | 401 + `access_denied` | as specified | `test_chat_without_session_401` |
| Extra field | `customer_id` in body | 422, no logic runs | as specified | `test_chat_extra_field_422` |
| Wrong role | advisor session | 403 `Customers only` | as specified | `test_chat_rejects_non_customer_role_403` |

## Roles and queue

| Scenario | Expected | Observed | Test |
|---|---|---|---|
| Customer lists queue | 403 + `access_denied` | as specified | `test_roles_queue.py::test_customer_cannot_list_queue_403` |
| Advisor lists queue | 403 (admin endpoint) | as specified | `test_admin.py::test_advisor_cannot_reach_admin_403` |
| Mock handoff in queue | 1 case, `Escalated`, summary only (no transcript/profile) | as specified | `test_handoff_appears_in_queue_with_summary_only` |
| Claim then resolve | owner set, `InReview`, then `Resolved`, queue empties | as specified | `test_advisor_claims_and_advances_case` |
| Metrics match audit | counts equal events; no message text anywhere | as specified | `test_admin.py::test_metrics_match_audit_events`, `test_no_message_text_in_audit` |

## UI, themes, languages

| Scenario | Expected | Observed | Test |
|---|---|---|---|
| Role landing | customer→chat, advisor→queue, admin→panel | manual, as specified | browser |
| Receipt card | verified check, facts, 5-step timeline | manual, as specified | browser |
| `es-AR` fallback | override where present, `es-419` elsewhere | as specified | `test_i18n.py::test_regional_fallback_to_base` |
| `pt-BR` complete | all base keys translated | as specified | `test_portuguese_is_complete` |
| Storage hygiene | only `sentinel-theme` in localStorage; no `innerHTML` | as specified | `test_only_theme_key_in_browser_storage` |
