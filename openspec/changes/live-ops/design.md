---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Design

## Decisions

1. **Fail on a missing salt.** A generated salt dies with the deploy and breaks correlation.
2. **One script for the checks.** `scripts/e2e_check.py` serves the gate (local) and the link. It has three modes: the cases, the credentials and `--access-check`.
3. **Local and remote modes.** On a loopback URL the script starts a local app with a clean SQLite file and the Gold mock, as `scripts/manual_test_replay.py` does. On a remote URL it starts nothing.
4. **Entry by persona or by password.** If `GET /api/v1/auth/demo` answers 200, the script uses the persona. If it answers 404, which is the public link, it uses the judge credentials.
5. **Credentials by file.** `SENTINEL_E2E_CREDENTIALS_FILE` names the sheet that `scripts/make_judge_users.py` writes (`deploy/judge-users/passwords.csv`). The script never prints or logs a password. Without the variable on a remote URL it stops before any request.
6. **One failed attempt for each login.** The judge logins have the same names as the documented fixture logins. A failed attempt counts for the lockout, which lasts 15 minutes. The access check makes one failed attempt for each login.
7. **Order on the link.** Run `--access-check`, then the cases, then `deploy/azure/reset-state.sh`. A second run of the cases on a dirty state can fail, because the charge of the normal case is already in review.
8. **The phone check asserts.** It checks no horizontal scroll at 390 px, the chat form, the build line and the closed judge guide. `scripts/capture_ui_product.py` starts its own app and enters by persona, so the check uses its Playwright setup with a base URL and a login.
9. **Script name in one constant.** `manual_test_replay.py` is the new name of `felix_replay.py`.

## Risks / Trade-offs

- **Log ingestion delay:** queries run a few minutes after the traffic.
- **The deploy recreates the app:** done before recording, never during.
- **A failed login can lock a judge account:** one attempt for each login, and run it from the owner machine.
