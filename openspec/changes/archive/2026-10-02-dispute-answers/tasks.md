# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [010](../../../docs/build/decisions/010-fraud-handoff-rule.md), [011](../../../docs/build/decisions/011-high-amount-threshold.md), [021](../../../docs/build/decisions/021-dispute-policy-sources.md). All paths are under `sentinel-ai-core/` unless stated.

## 1. Remember the last decision

- [x] 1.1 Add `last_decision` (rule id, candidate id, policy version, values snapshot) to the conversation state and to its JSON read and write, with a default for stored conversations. Evidence: `tests/test_state_sqlite.py` loads an old payload without the field.
- [x] 1.2 Record it at the single point where every policy decision passes, only for rules that have an explanation, so confirmations and case creation do not overwrite it. Evidence: `tests/test_policy_gate.py` cases for replace and no-overwrite.
- [x] 1.3 Build the values snapshot for `window.expired` from the country file and the verified candidate: window days, charge date, last eligible date, age in days, synthetic flag. Evidence: `tests/test_policy_engine.py` case on day 90 and day 91.

## 2. Answer the why follow-up

- [x] 2.1 Add the deterministic recognition for es-419 and pt-BR, active only while a last decision exists and only when no charge is named. Evidence: `tests/test_explanation.py` with a table of phrasings per language, including colloquial forms, and the negatives.
- [x] 2.2 Return an explanation from the stored decision without calling the policy engine, the lookup tool or the model. Evidence: `tests/test_explanation.py` asserts none of the three is called.
- [x] 2.3 Map the three kinds: rule and values for window, status and already disputed; one fixed sentence for `amount.high`, `fraud.score` and `fraud.claim`; a what-I-can-do answer with no decision. Evidence: `tests/test_explanation.py`.

## 3. Contract and page

- [x] 3.1 Add the `explanation` variant to the strict chat schema and to `demo_chat.py`, carrying key, rule id and verified values and nothing else. Evidence: `tests/test_contract.py` rejects extra fields and a `customer_id`.
- [x] 3.2 Add the texts in `es-419` and `pt-BR` with placeholders, the demonstration label read from `synthetic`, and the fixed safety sentence. Back-translate the pt-BR ones as in [017](../../../docs/build/decisions/017-portuguese.md). Evidence: `eval/review/` note with the back-translation.
- [x] 3.3 Render the explanation in the page, filling placeholders from the carried values. Evidence: `tests/test_ui.py` and a manual run recorded in `team/chat-manual-tests.md` as MT-05 retest.
- [x] 3.4 Extend `tests/test_policy_texts.py` so no explanation text contains a written number and none contains the word fraud. Evidence: the same file.

## 4. Safety evidence

- [x] 4.1 Add attacks that probe the thresholds and the fraud rule by repeated why questions, in es-419 and pt-BR. Evidence: new cases under `tests/adversarial/`.
- [x] 4.2 Run `SENTINEL_WRITE_EVIDENCE=1 python -m pytest tests/adversarial -q` and keep the new run, never edit an old one. Evidence: `evidence/adversarial/<run-id>/summary.json` with `unsafe_outcome_rate` and its denominator.

## 5. Document and close

- [x] 5.1 Retest MT-05 with the real model and a fresh session; record the result in `team/chat-manual-tests.md`. Evidence: that file.
- [x] 5.2 Write the justification sentences for the README limitations and the slide: demonstration policy, real windows and bank obligations as production path, Colombia not found. Evidence: README section and a link to [021](../../../docs/build/decisions/021-dispute-policy-sources.md).
- [x] 5.3 Update `docs/rationale/policy-sources.md` (the explanation now reads `window_days`), the requirement evidence for REQ-0033, and mark task 22 progress in `team/tasks.md`. Evidence: those files.
- [x] 5.4 Run the existing test suite and report counts, including any failure. Evidence: pytest output pasted in the commit body.
