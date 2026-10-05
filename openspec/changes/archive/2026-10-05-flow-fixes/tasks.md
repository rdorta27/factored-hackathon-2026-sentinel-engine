---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md), [015](../../../docs/build/decisions/015-handoff-delivery.md), [020](../../../docs/build/decisions/020-req-0001-context-tradeoffs.md). Source: the manual test by Felix on 2026-10-04. Paths are under `sentinel-ai-core/`. Run `python3 -m pytest -q` after each group.

## 1. Regression tests first

- [x] 1.1 Write one failing test per defect: stuck handoff, changing reason, dispute status opens a case, correction with the box open, box for an already disputed charge, date with no match. Evidence: `tests/test_flow_fixes.py`. Seven tests fail on `main`. The already-disputed test and the length test pass, because `SessionBoundLookup._mark` and the schema already cover them; they stay as guards.

## 2. Fixes

- [x] 2.1 Keep the handoff reference per case; answer "case with an advisor (`HO-…`)" only for the same case; let other requests continue; never rewrite a filed reason. Evidence: `tests/test_flow_fixes.py`; the person rule fires for `Intent.PERSON` only, and `finish_turn` reuses the filed reference and reason.
- [x] 2.2 Add the dispute-status check before the model, in es-419 and pt-BR, that answers from the case store or says no case exists. Evidence: `tests/test_flow_fixes.py`; the reply is an `explanation` with `values.case_id` and `values.case_status`.
- [x] 2.3 Let a correction close the confirm box and ground the new candidate. Evidence: the "1.000 then 320" test opens the `TXN-1006` charge.
- [x] 2.4 Warn about an open dispute before the box. Evidence: the already-disputed test passes; `SessionBoundLookup._mark` already reads the case store.
- [x] 2.5 Name the searched date when no charge matches. Evidence: `tests/test_flow_fixes.py`, `values.searched_date`, and the keys `charge.notFoundDate` in es-419 and pt-BR.
- [x] 2.6 Verify the 2000-character limit in `schemas/chat.py` and add a test that 2001 characters return 422. The page already sets `maxlength="2000"`, and `bank-ui` owns `static/`. Evidence: a test that 2001 characters return 422.
- [x] 2.7 Add the `trace_id` to the 429 body. The error bubble already shows `body.trace_id`, and `bank-ui` owns `static/`. Evidence: a test of the body in `tests/test_flow_fixes.py` and `tests/test_rate_limits.py`.

## 3. Evidence

- [x] 3.1 Run the adversarial suite and `eval.run verify 2024Q4-resolution-v2`; freeze a new resolution run if the replay changes. Evidence: the run `evidence/adversarial/20261004T195343Z` with `totals.unsafe_outcome_rate` = `0/42`, and `[verify] 2024Q4-resolution-v2: matches the frozen summary`, so no new resolution run.
- [x] 3.2 Write `scripts/felix_replay.py`. It replays the ten points of Felix against the app over HTTP, on a clean SQLite file and a new session per point. It uses port 8002 and writes a pass/fail table to `team/chat-manual-tests.md` and to the screen. Points 4 and 8 depend on the model: mark them "out of scope (router-v3)". Evidence: the script, the reusable client `scripts/sentinel_client.py`, and the table in `team/chat-manual-tests.md` (8 pass, 2 out of scope).
- [x] 3.3 G1: Rubén reads the report of task 3.2. Evidence: the report in `team/chat-manual-tests.md`; the conversation page and REQ-0001, REQ-0006 and REQ-0043 carry the new behaviour.
