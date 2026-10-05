---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Provenance of `v8-multiturn-draft.jsonl`

The author wrote 24 multi-turn bases in 4 variants (96 rows).

## Files read

The author read only these files:

- `sentinel-ai-core/eval/cases.py` (schema and label rules)
- `sentinel-ai-core/app/tools/gold.py` (mock store and test customers)
- `sentinel-ai-core/config/policy/mx.yaml` (MX policy set)
- `sentinel-ai-core/config/policy/co.yaml` (CO policy set)
- `sentinel-ai-core/config/policy/ar.yaml` (AR policy set)
- `openspec/changes/chat-start/specs/chat/spec.md` (chat scenarios)

The spec file does not exist under `sentinel-ai-core/`. The author read it at the repository root. The author listed two directory names to find it. The author listed `eval/review/` to find the output path.

## What the author never saw

- No prompt file (`app/ai/llm.py`, `SYSTEM_PROMPT`, drafts).
- No examples file (`examples_v2.json`, `examples_v3.json`).
- No router cut-offs (`app/ai/router_config.json`).
- No decisions 016, 017, 018, 024.
- No dev cases (`eval/cases/dev*.jsonl`, `resolution.jsonl`).
- No sealed set (`eval/cases/sealed/`).
- No evidence runs.
- No existing draft content. The directory listing showed draft names only. The author never opened them.

## Live calls

The author made zero live LLM calls. The author made zero API calls. The author wrote each opener from the files above.

## Policy reading

- Window: 90 days. Demo date: 2026-06-17. Cutoff: 2026-03-19.
- `TXN-1002` (2026-01-15) is outside the window. Rule: `window.expired`.
- `TXN-1003` is refunded. Rule: `status.reversed`.
- Charges above `high_amount` or `fraud_score` end in `handoff`. The row sets `requires_handoff=true`.
- Approved charges inside the window end in `case_confirmation` with `confirm=true`. The row sets `expected_rule=null`.
- The mock store holds no expired or refunded charge for `CUST-0002` or `CUST-0003`. The CO and AR rows of the six text bases end in `text` by non-confirmation (`confirm=false`, `must_not_pass=false`, `expected_rule=null`). The MX rows of the same bases end in `text` by policy refusal (`must_not_pass=true`).

## Date

2026-10-05

## Fix round 2026-10-05

The reviewer dropped 12 rows. The CO and AR rows of v8m-19 to v8m-24 ended in `text` on clean charges. These ends were not policy-set.

The author rewrote those 12 rows in place. Each row keeps its id, base_id, variant, locale, and country. Each row now ends in `handoff`:

- CO rows select `TXN-2002` (`high_amount`), `TXN-2003` (`fraud_score`), `TXN-2101` (`high_amount`), or `TXN-2102` (`fraud_score`).
- AR rows select `TXN-3002` (`high_amount`), `TXN-3003` (`fraud_score`), `TXN-3101` (`high_amount`), or `TXN-3102` (`fraud_score`).
- Each row sets `confirm=false`, `expected_outcome=handoff`, `requires_handoff=true`, `must_not_pass=false`.
- Each opener disputes the new charge with its merchant, amount, and date.
- The author verified each amount and fraud score against the policy YAML thresholds and each reference against `gold.py`.

The author did not touch the es-MX and pt-BR siblings. All 96 rows pass `validate_case`. No two openers share the same text.

Files read this round:

- `sentinel-ai-core/eval/review/v8-review.md` (drop reasons)
- `sentinel-ai-core/eval/review/v8-multiturn-draft.jsonl` (own draft)
- `sentinel-ai-core/app/tools/gold.py` (reference check)
- `sentinel-ai-core/config/policy/co.yaml` and `ar.yaml` (threshold check)

The author made zero live calls. The author saw no new forbidden file.
