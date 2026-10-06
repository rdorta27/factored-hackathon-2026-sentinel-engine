---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Proposal

## Why

The demo has a one-click entry. `POST /api/v1/auth/demo/{persona}` signs a visitor in with no password. The same flag, `SENTINEL_DEMO_AUTH=1`, loads the advisor account. The documented advisor password (`Advisor-001`) and the customer password (`Testpass-001`) sit in the public README. On a public link, anyone who reads the repository can open the advisor view of every ticket.

The brief asks for authentication with a trusted test session. A persona id proves nothing about identity (the README says so). Passwords must reach the evaluators by the submission email, not by the repository, the slides or the video.

This change removes the passwordless entry from the public link and gives the judges their own credentials. It cites REQ-0027, REQ-0031 and REQ-0035.

## What Changes

- **Flag.** A new flag, `SENTINEL_DEMO_PERSONAS`, controls the one-click route. It follows `SENTINEL_DEMO_AUTH` when unset, so local runs and tests stay the same. The public link sets it to `0`. The route and the persona list answer 404.
- **Judge users.** A script writes a users file with random passwords for the customer accounts of the four demo cases and for one advisor. The file holds only hashes. The plain passwords go to an ignored sheet that the owner pastes in the email.
- **Deploy.** The file goes to the Azure Files share. The app reads it with `SENTINEL_USERS_PATH`. The documented fixture passwords do not work on the public link.
- **Banner.** The "simulated data" notice shows whenever Gold is a mock. It no longer depends on the one-click entry.
- **Docs.** The README, the decisions 009 and 019, `what-is-real.md`, `mocks.md` and REQ-0027 say that the public link uses emailed credentials. The delivery page holds the email template, with no real value.
- **Checks.** After the final redeploy, the link rejects the fixture passwords and accepts the judge credentials.

## Capabilities

### New Capabilities
- `judge-access`: how the public link authenticates evaluators.

### Modified Capabilities
(none)

## Impact

- `sentinel-ai-core/app/session/router.py`, `app/static/`, `scripts/`, `deploy/azure/`, the READMEs, `docs/`, the decisions 009 and 019, REQ-0027 and `team/`.

## Non-goals

- A real identity provider, passwords in the repository, or a password reset flow.
- Changing the login lockout, the session length or the advisor permissions.
- Removing the one-click entry from local runs and tests.
