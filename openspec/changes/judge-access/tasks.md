---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md), [019](../../../docs/build/decisions/019-azure-container-apps.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

Runs before gate G3. Starts from `origin/main`. Never write a plain password in a tracked file.

## 1. Entry without a password

- [x] 1.1 Add `SENTINEL_DEMO_PERSONAS` in `app/session/router.py`. When it is `0`, `GET /api/v1/auth/demo` and `POST /api/v1/auth/demo/{persona}` answer 404. When it is unset, it follows `SENTINEL_DEMO_AUTH`. Evidence: tests for both cases, and `tests/test_demo_auth.py` still green.
- [x] 1.2 Show the "simulated data" notice on the entry page when `gold_source` is `mock`, whether or not the one-click entry exists. Change the text of `demoBannerText` so it does not say "no password". Keep the id `demo-banner` and its `data-testid`. Add the new keys to `es-419.json` and `pt-BR.json`. Evidence: `app/static/` and a test.
- [x] 1.3 Read the login lockout in `app/session/limits.py` (HTTP 429). The lock lasts 15 minutes (`LOCKOUT_DURATION`). Read the number of failures that triggers it. Write both in the email template (task 3.3). Change nothing. Evidence: the numbers in `docs/build/delivery.md`.

## 2. Judge credentials

- [x] 2.1 Write `scripts/make_judge_users.py`. It writes a users file with random passwords for one shared set: three customer logins (CUST-0001, CUST-0002 and CUST-0003 of the persona map) and one advisor. All judges use the same set (decision of 2026-10-05). It uses `hash_password` of `app/session/security.py`. It writes the hashes to a folder that git ignores and the plain passwords to an ignored sheet. It prints no password. Add both paths to `.gitignore`. Evidence: the script, a test that the users file holds no plain password, and `git check-ignore` output.
- [x] 2.2 Check that each login reaches the expected case: the normal and ambiguous cases on one customer, the high amount case and the not-me case on the other two. Evidence: a test with the generated file.
- [x] 2.3 Add `deploy/azure/upload-users.sh`: it copies the users file to the Azure Files share. Make `deploy/azure/deploy.sh` set `SENTINEL_USERS_PATH` to the file and `SENTINEL_DEMO_PERSONAS=0`. Document both in `deploy/azure/README.md`. Evidence: a dry run that prints the commands.

## 3. Documentation

- [x] 3.1 In the README and `sentinel-ai-core/README.md`, say that the documented credentials are for local runs and that the public link uses the credentials of the submission email. Remove the sentence that the page needs no password. Evidence: the two files.
- [x] 3.2 Update decisions 009 and 019, the login row of `docs/architecture/what-is-real.md` and `docs/architecture/mocks.md`, and the card of REQ-0027. Evidence: those files.
- [x] 3.3 Add the submission email template to `docs/build/delivery.md`: the repository, the link, the slides, the video, and a credentials block with placeholders. Add the lockout rule of task 1.3 and a line that no password goes in the slides or the video. Evidence: the file.

## 4. Checks

- [x] 4.1 Run the full suite. Evidence: the pass count in the commit body.

## 5. Requirements and team

- [x] 5.1 Update the card of REQ-0027 with the new evidence. Change a status only when its evidence exists. Evidence: `docs/requirements/non-functional.md`.
- [x] 5.2 Update `team/tasks.md` and `team/pending-decisions.md`. Evidence: the two files.

## Moved to other plans

These checks need the final redeploy, the final site or the video script. They live in other changes. This plan closes when groups 1 to 3 and task 4.1 are done.

| Old task | New task | What |
|---|---|---|
| 2.4 | `live-ops` 1.5 | `scripts/e2e_check.py` reads the judge credentials from the sheet (the file belongs to `live-ops`) |
| 4.2 | `post-freeze` 4.6, `live-ops` 1.7 | The access check on the link after the final redeploy. `live-ops` writes the check |
| 4.3 | `docs-followups-2` 6.1 | The search for a password in the slides, the site and the video script |
