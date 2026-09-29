# Proof checks: refine-mvp-gold-layer-proof-of-work

Verified 2026-09-29 with `pytest -q` (86 passed) on Python 3.12.10, plus
browser and `/docs` walkthrough against one `uvicorn` process. Extends the
`add-chat-roles-trust-ui` trust matrix (`trust-checks.md`).

Golden-rule alignment: the mock orchestrator returns intent plus a Gold
reference only; amounts, merchants, dates, eligibility, and state changes all
come from backend code. No SQL from the LLM, no lakehouse writes.

## Disputes endpoint (`POST /api/v1/disputes/create`, role customer)

| Scenario | Request | Expected | Observed | Test |
|---|---|---|---|---|
| Eligible | `TXN-1001` + fresh key | 201 with all five PoW elements, `verified=true`, `source=mock` | as specified | `test_disputes.py::test_eligible_creates_case_with_proof` |
| Stale | `TXN-1002` | 422, 90-day reason, no case created | as specified | `test_stale_refused_with_reason`, `test_refusal_creates_no_case` |
| Refunded | `TXN-1003` | 422, refund reason | as specified | `test_refunded_refused` |
| Prior dispute | `TXN-1004` | 422, prior-dispute reason | as specified | `test_prior_dispute_refused` |
| Unknown | `TXN-0000` | 422, not-found reason | as specified | `test_unknown_reference_refused` |
| Replay | same key twice | same `case_id`, one case in store | as specified | `test_duplicate_key_replays_without_new_case` |
| Receipt | `GET .../CASE-*/receipt` | 200 plain text with facts, rule, SLA, simulated labels | as specified | `test_receipt_download` |
| Receipt unknown | `CASE-9999` | 404 | as specified | `test_receipt_unknown_404` |
| No session | no cookie | 401 | as specified | `test_create_without_session_401` |
| Extra field | `amount` in body | 422 | as specified | `test_create_extra_field_422` |
| Advisor creates | advisor session | 403 | as specified | `test_advisor_cannot_create_403` |

## Chat rewire

| Scenario | Expected | Observed | Test |
|---|---|---|---|
| Normal dispute | confirmation facts equal `TXN-1001` Gold row, PoW fields present | as specified | `test_chat.py::test_normal_case_returns_verified_confirmation` |
| Chat equals service | hold, rule, SLA, queue identical to endpoint result | as specified | `test_chat_confirmation_matches_disputes_service` |
| Stale via chat | `handoff` with window reason, escalated case with real facts | as specified | `test_stale_charge_chat_returns_handoff` |
| Refunded via chat | `handoff` | as specified | `test_refunded_charge_chat_returns_handoff` |
| Broken store | `handoff`, never confirmation | as specified | existing broken test, still green |

## Proof-of-Work card (browser)

| Scenario | Expected | Observed |
|---|---|---|
| Normal dispute in UI | card shows hold, rule plus Art. 4, SLA date, receipt download link, queue status | manual, as specified |
| Receipt download | click downloads `RCPT-CASE-*.txt` plain text | manual, as specified |
| Language switch | new card labels translated in `es-419` and `pt-BR`, fallback intact | `test_i18n.py` green |
