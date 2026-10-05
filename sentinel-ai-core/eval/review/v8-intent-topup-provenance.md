# v8 intent top-up provenance

Date: 2026-10-05.

## Files read

- `eval/cases.py`
- `eval/cases/sealed_v8/intent-draft.jsonl`
- `eval/cases/sealed_v8/README.md`

## Isolation

- Network calls: zero.
- No API calls.
- Never saw prompt files.
- Never saw examples.
- Never saw cut-offs.
- Never saw amendment text.
- Never saw dev cases.
- Never saw the v7 sealed set.
- Never saw mock store.
- Never saw policy YAMLs.
- Never saw evidence files.
- Wrote only `eval/review/v8-intent-topup.jsonl`.
- Wrote only `eval/review/v8-intent-topup-provenance.md`.
- Did not touch `eval/cases/sealed/`.
- Did not touch `seal.json`.
- Did not touch `measured.json`.
- Did not touch `evidence/`.

## Output

- 5 new bases (v8i-49 to v8i-53).
- 4 variants per base.
- 20 rows total.

## Fix round 2026-10-05

- Read only the v8i-44-pt-BR drift note in `eval/review/v8-review.md`.
- No network calls.
- Wrote one corrected row to `eval/review/v8-intent-fix.jsonl`.
- Did not touch `eval/cases/sealed/`.
- Did not touch `seal.json`.
- Did not touch `measured.json`.
- Did not touch `evidence/`.
