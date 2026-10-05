# v8 attack block and noisy twins — provenance

Date: 2026-10-05. Isolated author of the attack block and noisy twins.

## Files read (only)

- eval/cases.py (schema, FAULTS, VARIANTS, PERTURBATIONS)
- tests/adversarial/test_a_injection.py (attack categories)
- tests/adversarial/test_b_access.py (attack categories)
- tests/adversarial/test_c_session.py (attack categories)
- tests/adversarial/test_d_tools.py (attack categories)
- tests/adversarial/test_e_ambiguity.py (attack categories)
- tests/adversarial/test_f_decision_disclosure.py (attack categories)
- eval/cases/sealed_v8/intent-draft.jsonl (twin sources v8i-01..v8i-13)
- eval/cases/sealed_v8/README.md (staging status)

## Isolation

- Zero network calls. Zero API calls.
- Never saw: app/ai/llm.py or any prompt, any examples file, router cut-offs, decisions 016/017/018/024, eval/cases/dev*.jsonl, eval/cases/resolution.jsonl, eval/cases/sealed/, the mock store (gold.py), policy YAMLs, evidence/.
- Wrote only: eval/review/v8-attack-draft.jsonl, eval/review/v8-attack-provenance.md.
- Never touched: eval/cases/sealed/, seal.json, measured.json, evidence/.

## Outputs

- eval/review/v8-attack-draft.jsonl: 136 rows, all pass validate_case.
- Attack: 84 rows, v8a-01..84, held_out, tags ["adversarial"], 7 categories x 12 (3 per variant; pt-BR uses country MX).
- Twins: 52 rows, bases v8i-01..v8i-13 x 4 variants, tags ["noisy"], one perturbation each (date_shift 13, amount_shift 13, truncated_name 13, self_correction 13), labels identical to source.
