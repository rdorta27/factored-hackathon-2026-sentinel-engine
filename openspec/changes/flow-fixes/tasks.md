---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md), [015](../../../docs/build/decisions/015-handoff-delivery.md), [020](../../../docs/build/decisions/020-req-0001-context-tradeoffs.md). Source: the manual test by Felix on 2026-10-04. Paths are under `sentinel-ai-core/`. Run `python3 -m pytest -q` after each group.

## 1. Regression tests first

- [ ] 1.1 Write one failing test per defect: stuck handoff, changing reason, dispute status opens a case, correction with the box open, box for an already disputed charge, date with no match. Evidence: `tests/test_flow_fixes.py` fails on `main`.

## 2. Fixes

- [ ] 2.1 Keep the handoff reference per case; answer "case with an advisor (`HO-…`)" only for the same case; let other requests continue; never rewrite a filed reason. Evidence: tests 1.1 pass.
- [ ] 2.2 Add the dispute-status check before the model, in es-419 and pt-BR, that answers from the case store or says no case exists. Evidence: tests with positive and negative phrases.
- [ ] 2.3 Let a correction close the confirm box and ground the new candidate. Evidence: the "1.000 then 700" test opens the 700 charge.
- [ ] 2.4 Warn about an open dispute before the box. Evidence: test.
- [ ] 2.5 Name the searched date when no charge matches. Evidence: test and locale keys in es-419 and pt-BR.
- [ ] 2.6 Verify the 2000-character limit in `static/index.html` and `schemas/chat.py`. Evidence: a test that 2001 characters return 422.
- [ ] 2.7 Add the `trace_id` to the 429 body and show it in the error bubble. Evidence: a test of the body and `static/app.js`.

## 3. Evidence

- [ ] 3.1 Run the adversarial suite and `eval.run verify 2024Q4-resolution-v2`; freeze a new resolution run if the replay changes. Evidence: a new `evidence/adversarial/` run and the verify output in the commit body.
- [ ] 3.2 Repeat the manual test of Felix and record the result. Evidence: `team/chat-manual-tests.md`.
