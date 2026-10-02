# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [008](../../../docs/build/decisions/008-account-inquiry-scope.md), [017](../../../docs/build/decisions/017-portuguese.md), [020](../../../docs/build/decisions/020-req-0001-context-tradeoffs.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

## 1. Narrowing (grounding.py, step.py)

- [ ] 1.1 Soft facts in `app/ai/grounding.py`: merchant tokens with stop words and four-letter prefix, relative dates for es-419 and pt-BR from the reference date, repeated-charge phrases. Evidence: `tests/test_grounding.py` over every mock merchant ("cafetería" to "Cafe Central"), each date phrase at 2026-06-17, a duplicated pair.
- [ ] 1.2 Narrow and rank the clarification candidates in `step` without touching exact selection; add the not-found key in both locales. Evidence: tests that one soft match is a clarification, never a confirm box, and that an unknown merchant gets the not-found text.
- [ ] 1.3 Development cases with expected charge ids (the MT-06 messages in four variants) and an offline report of right-charge-shown and not-found-said, before and after. Evidence: cases under `eval/cases/` and the numbers in the commit body.

## 2. Guards (new guard module, step.py)

- [ ] 2.1 Extraction and injection pattern sets with positives and negatives, accent-insensitive, voseo included. Evidence: unit tests; a test running the sealed attack messages through both checks (four extraction ids fire, five mixed ids skip the refusal).
- [ ] 2.2 Wire both before the model: extraction returns the offer with its key, increments the out-of-scope streak and logs `extraction_refused`; injection logs `injection_suspected` and continues. Add the refusal text in both locales, pt-BR back-translated. Evidence: tests that the model is not called on extraction, the third attempt hands off, and replies are unchanged on injection; note under `eval/review/`.

## 3. Read budget (bound.py)

- [ ] 3.1 Run Gold reads under `SENTINEL_GOLD_TIMEOUT_S` with a timeout record and the existing failure path. Evidence: a slow-fake test ending in a handoff without case number within the total budget.

## 4. Attack evidence and close

- [ ] 4.1 Rewrite A3, A4b and D4 to the contract, drop `xfail`, mark `blocked_verified`; freeze one run with `SENTINEL_WRITE_EVIDENCE=1 python -m pytest tests/adversarial -q`. Evidence: `evidence/adversarial/<run-id>/summary.json` with no `no_defense_yet` left.
- [ ] 4.2 Retest MT-05 and MT-06 in a fresh session; update README safety and narrowing lines, REQ-0021 evidence and `docs/build/security.md`. Evidence: `team/chat-manual-tests.md` and those files.
