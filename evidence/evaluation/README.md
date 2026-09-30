# Evaluation evidence

Frozen aggregates the evaluation runner consumes. Flow evidence chose the
flow; this folder feeds the runner with the label universe, case mix, intent
mix and reference thresholds.

- `eval_measure.py` — stdlib script (`run` | `verify` | `derive`).
- `method.md` — window, cut and guarantees.
- `<run-id>/` — write-once frozen runs (`summary.json`, `method.md`, `MANIFEST.md`, `README.md`).
- `test_eval_measure.py` — synthetic-data checks (guard, verify, derive).
