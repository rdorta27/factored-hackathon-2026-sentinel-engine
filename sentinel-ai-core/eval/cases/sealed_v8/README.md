---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Sealed v8 set (sealed 2026-10-05)

Hash `3b4a472bb8071a24205129ef5c8b75783ed439be313b5f91ec6782a8f2adf645`.
Record: `seal.json` in this folder. 444 rows, 77 main bases.
Variants complete per base: es-MX 77, es-CO 77, es-AR 77, pt-BR 77.
Intents over main: charge 184, missing 40, status 28, out_of_scope 28, person 28.
Noisy twins 52, attacks 84.

## Files

- `intent.jsonl`: intent block (53 bases in four variants).
- `multiturn.jsonl`: multi-turn block (24 bases, ends set by policy).
- `attacks.jsonl`: attack block (84 rows, seven categories).
- `noisy.jsonl`: noisy twins (52 rows, four perturbations).
- `seal.json`: the seal record. The v7 seal and `measured.json` stay unchanged.

## Provenance

- Five isolated subagent sessions wrote and reviewed the blocks.
- Notes: `eval/review/v8-intent-provenance.md`, `v8-multiturn-provenance.md`, `v8-attack-provenance.md`, `v8-intent-topup-provenance.md`, `v8-review.md`.
- Review flagged 13 rows; the authors rewrote all 13 (12 multi-turn ends, 1 pt-BR drift). Zero rows dropped. No person wrote or reviewed a case.
- Limit: all five sessions share one model family. Author and reviewer share its biases. The submission states it.

## Rule

No run reads this folder until the frozen `2024Q4-eval-v8` measurement.
`measured.json` holds no entry for the v8 hash until then.
