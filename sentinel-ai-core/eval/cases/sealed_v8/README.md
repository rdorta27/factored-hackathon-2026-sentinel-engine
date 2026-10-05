---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Sealed v8 staging (draft, not sealed)

This folder stages the second sealed set for `2024Q4-eval-v8`.
It is a draft. It is not sealed. No hash covers it.
`eval/cases/seal.json` still holds only the v7 seal.
`eval/measured.json` still holds only the v7 entry.

## What is here

- `intent-draft.jsonl`: a copy of `eval/review/v8-intent-draft.jsonl`.
  48 bases in four variants (192 rows).
  Schema valid per `eval/cases.py` (checked 2026-10-05).
  Provenance: `eval/review/v8-intent-provenance.md`.

## What is missing

- Multi-turn block (task 2.2): needs an isolated author.
- Attack block and noisy twins (task 2.5): needs an isolated author.
- Review and back-translation (task 2.3).
- Seal under a new hash (task 2.4): only after review.
  Sealing must leave the v7 entry unchanged.

## Rule

No run reads this folder until the seal.
Selection and rehearsal read development only.
