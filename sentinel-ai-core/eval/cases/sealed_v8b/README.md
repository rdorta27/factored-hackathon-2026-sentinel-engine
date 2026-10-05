---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Sealed v8 top-up set (sealed 2026-10-05)

Hash `ebdd937e5480014d7881d9c6e99cce79066ebe1273a5ed5fe55d518fe43ef19b`.
Record: `seal.json` in this folder. 92 rows, 23 bases.
Variants complete per base: es-MX 23, es-CO 23, es-AR 23, pt-BR 23.
New bases per thin intent: out_of_scope 6, person 6, status 5.
Flavors: 2 ambiguous, 2 mixed-language, 2 dual-intent bases.

## Files

- `topup.jsonl`: the top-up block (23 bases in four variants).
- `seal.json`: the seal record. The v7 and v8 entries stay unchanged.

## Why a separate seal

The top-up supplements the v8 set. It holds no attacks and no twins.
So the v7 minimums (70 bases, attacks, twins) do not fit it.
The seal call uses minimums of 20 bases and 4 rows per intent.
The real gate is the test: 6 new bases for each thin intent, the flavors
present, every base complete in four variants, and the reviewed drop applied.

## Provenance

- One isolated subagent session wrote the block from the contract definitions only.
- One isolated review session checked labels, near-copies against v8, and back-translations.
- Review dropped 1 base (`v8t-13`, balance asked as `status`, near-copy of `v8i-38`).
- Notes: `eval/review/v8-topup-provenance.md`, `v8-topup-review.md`.
- Limit: both sessions share one model family with the v8 authors.

## Rule

No run reads this folder until the frozen `2024Q4-eval-v8` measurement.
`measured.json` holds no entry for this hash until then.
