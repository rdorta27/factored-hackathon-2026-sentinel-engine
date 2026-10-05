---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [006](../../../docs/build/decisions/006-frontend.md), [019](../../../docs/build/decisions/019-azure-container-apps.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

Runs before gate G3. Starts from `origin/main`. Do not rename an id, a `data-testid` or an i18n key. Add each new key to `es-419.json` and `pt-BR.json`.

## 1. Example buttons

- [x] 1.1 Change the text of `demoHint` to "Try an example" in `index.html`, "Prueba con un ejemplo" in `es-419.json` and "Experimente um exemplo" in `pt-BR.json`. Keep the key. Evidence: the three files and `tests/test_demo_prompts.py`.
- [x] 1.2 Show the example buttons and their label only when `demoAvailable` is true, the condition of the demo banner. Evidence: `app/static/app.js` and a test for both cases.

## 2. Build line

- [x] 2.1 Add a footer line with `data-testid="build-info"`. It reads `GET /api/v1/health` once and shows the model, the prompt version, the first 8 characters of `bundle_hash` and `gold_source`. Hide it if the request fails. Evidence: `index.html`, `app.js`, `styles.css`.
- [x] 2.2 Add the label keys to `es-419.json` and `pt-BR.json` and test that the line shows the fields of a mocked health response and stays hidden on a failure. Evidence: the test.

## 3. Guide for the judge

- [x] 3.1 Write the guide text in `es-419.json` and `pt-BR.json`. It says that the public link needs the credentials of the submission email (see `judge-access`). The "simulated data" banner belongs to `judge-access` 1.2: do not change it here. The guide has: the three cases to try (normal, ambiguous, person), what to look for in each, and the four simulated parts (Gold data, test login, demo advisor, synthetic policy), as in [what is real](../../../docs/architecture/what-is-real.md). Evidence: the two files.
- [x] 3.2 Add a collapsible panel on the entry page with `data-testid="judge-guide"`. It starts closed and does not move the persona cards on a phone. Evidence: `index.html`, `app.js`, `styles.css`.
- [x] 3.3 Test that the panel exists, starts closed and has text in both locales. Evidence: the test.

## 4. Checks

- [ ] 4.1 Run the UI tests, the demo tests and the contract tests: `tests/test_ui.py`, `tests/test_demo_prompts.py`, `tests/test_demo_pt_br.py`, `tests/test_contract.py` and the full suite. Evidence: the pass count in the commit body.
- [ ] 4.2 Run `scripts/capture_ui_product.py` and check the phone layout at 390 px. Replace the screens in the docs that show the entry page and the chat. Evidence: the new screens and the commit body.

## 5. Requirements and team

- [ ] 5.1 Update the card of REQ-0038 with the new evidence. Change a status only when its evidence exists. Evidence: `docs/requirements/frontend-backend.md`.
- [ ] 5.2 Update `team/tasks.md`. Evidence: the file.

## 6. Empty account and long lists

Found on 2026-10-05 in a local run. The server used the real Gold file, and the fixture users (`CUST-0001` to `CUST-0003`) exist only in the mock. The account had no charges. The panel of recent charges was empty with no message, and the only example button was "Quiero hablar con una persona". Each click opened a handoff ticket: 476 tickets for one customer.

- [ ] 6.1 Show a message in the panel of recent charges when the account has no charges, in `es-419.json` and `pt-BR.json` (new key `txEmpty`). Keep the ids and the `data-testid` of the panel. Evidence: `app/static/` and a test for the empty list.
- [ ] 6.2 Show the example buttons and their label only when the account has a charge or a repeated merchant. Do not show the single "talk to a person" button alone. Evidence: `app/static/app.js` and a test for an account without charges.
- [ ] 6.3 Show the five most recent items in "My claims", with "Show all (N)" for the rest. Do this in the page. Do not change the API. Evidence: `app/static/` and a test with more than five cases.
- [ ] 6.4 In `sentinel-ai-core/README.md`, say that a local run uses the real Gold file when it exists, that the fixture users exist only in the mock, and that the demo needs `SENTINEL_GOLD_SOURCE=mock`. Evidence: the README.

## Moved to `post-freeze`

The run of `scripts/e2e_check.py` needs the merged script of `live-ops` and the final build. It is task 1.2 of `post-freeze` (local) and task 4.3 (on the link). This plan closes when the other tasks are done.
