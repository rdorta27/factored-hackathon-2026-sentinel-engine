# Attack checks: sentinel-login

Verified 2026-09-29 with `pytest -q` (26 passed) on Python 3.12.10, plus manual
`/docs` walkthrough below. Each row maps to a test in `sentinel-login/tests/`.

| Attack | Request | Expected | Observed | Test |
|---|---|---|---|---|
| Wrong password | `POST /auth/login` `CUST-0001` + wrong | 401 `Invalid credentials` + `WWW-Authenticate` | 401, generic body | `test_auth_endpoints.py::test_login_wrong_password_generic_401` |
| Unknown user | `POST /auth/login` `CUST-9999` + any | Identical 401 body (no user oracle) | Identical to wrong-password case | `test_login_unknown_user_same_generic_401` |
| Credential stuffing | 5 failures then 6th | 429 + `login_locked` audit | 429 with lockout message | `test_auth_limits_audit.py::test_lockout_after_five_failures` |
| Forged token | `GET /auth/me` with invented cookie | 401 `Authentication required` + `access_denied` | 401 | `test_auth_endpoints.py::test_me_with_forged_token_401` |
| No session | `GET /auth/me` without cookie | 401 `Authentication required` | 401 | `test_me_without_cookie_401` |
| Expired session | Login with negative TTL, then `GET /auth/me` | 401 `Session expired` + `session_expired` audit | 401, expired event logged | `test_auth_limits_audit.py::test_expired_session_audited_as_session_expired` |
| Reused post-logout token | Login, logout, replay cookie | 401 | 401 | `test_auth_endpoints.py::test_logout_revokes_token` |
| Foreign identifier smuggled in body | Extra field in login body | 422, no auth logic runs | 422 | `test_auth_endpoints.py::test_smuggled_customer_id_rejected_with_422` |
| Injection-shaped message | N/A (no `/chat` in this change) | Deferred to the chat change | Deferred | — |
| Audit secrecy | All events | No password or full token in any record; `trace_id` 16 hex chars; `X-Trace-Id` header present | Verified | `test_auth_limits_audit.py::test_audit_record_shape_and_no_secrets` |

Manual `/docs` walkthrough: run `uvicorn app.main:app` from `sentinel-login/`,
open `/docs`, `POST /auth/login` with `{"customer_id": "CUST-0001",
"password": "Testpass-001"}` (demo-only credential), then `GET /auth/me`
(the browser re-sends the HttpOnly cookie automatically).
