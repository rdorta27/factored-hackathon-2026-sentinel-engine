# Tasks

Areas: [ml](../../../docs/build/areas/ml.md). Decisions: [016](../../../docs/build/decisions/016-router-models.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md). Paths are under `sentinel-ai-core/` unless stated.

## 1. Feasibility (stop here if it fails)

- [x] 1.1 Record one call per label on the served model with log-probabilities requested, JSON output and low reasoning; check the label token's alternatives are returned. Evidence: a note in `docs/build/decisions/016-router-models.md` with the request settings and the result; if unsupported, mark the rest of this change as not built.

## 2. Score and split

- [x] 2.1 Request log-probabilities in the transport, derive the label confidence, record it on the `understand` record, and keep calls without it working. Evidence: `tests/test_ai_router.py` with recorded fixtures with and without log-probabilities.
- [x] 2.2 Carve the `validation` split from development by base and write the choice rule in an 018 amendment, both committed before any fitting. Evidence: `tests/test_eval_cases.py` (no shared bases) and the decision file's commit order.

## 3. Cut-offs

- [x] 3.1 Fit on development, choose on validation, freeze a calibration run with the report per split. Evidence: `evidence/evaluation-runs/<calibration-run>/summary.json`.
- [x] 3.2 Load the cut-offs from a router configuration file behind a setting; a borderline or low label becomes `missing`; policy, handoff rules and the confirm box still decide. Evidence: tests that a borderline `charge` asks first, that a policy refusal still wins, and that the setting off behaves as v2.

## 4. Close

- [x] 4.1 Hand the cut-offs to `router-v3` for the `eval-v8` measurement; update README limitations and REQ-0016 evidence with the calibration result. Evidence: those files.
