# Tasks

## 1. Case set and loading

- [ ] 1.1 Define the JSONL case schema and a loader and validator; verify a case missing a label fails with its id named (evidence: `sentinel-ai-core/eval/cases.py`, tests; ref: decision 007)
- [ ] 1.2 Author the intent cases in `es-419` and `pt-BR` across charge, missing, out-of-scope and person, with edge and adversarial tags and the development/held-out split; verify no case id appears in both splits (evidence: `sentinel-ai-core/eval/cases/*.jsonl`; ref: REQ-0017)
- [ ] 1.3 Load the pinned label set from `eval/labels.json` and record its provenance with the run; verify the summary records the label set run id and hash (evidence: `sentinel-ai-core/eval/cases.py`; refs: REQ-0016, REQ-0017)

## 2. Shared metrics

- [ ] 2.1 Implement intent metrics (accuracy and per-class precision, recall and F1, plus the confusion matrix) by locale; verify against a hand-computed small example (evidence: `sentinel-ai-core/eval/metrics.py`, tests; ref: REQ-0016)
- [ ] 2.2 Implement the safety pass rate, the automation proxy and the stability agreement; verify each with a fixture (evidence: `sentinel-ai-core/eval/metrics.py`, tests; refs: REQ-0016, REQ-0020)
- [ ] 2.3 Implement the system metrics (safe resolution with the attempted share, containment, escalation quality, unsafe outcomes, p50/p95, cost per attempted and per resolution); verify the "not defined" case when there are no resolutions (evidence: `sentinel-ai-core/eval/metrics.py`, tests; ref: REQ-0055)

## 3. Component benchmark

- [ ] 3.1 Implement `bench_router.py` running the router and the keyword baseline over the same intent cases and computing the four pillars; verify both models ran the identical set (evidence: `sentinel-ai-core/eval/bench_router.py`, tests; ref: REQ-0020)
- [ ] 3.2 Implement stability with N repetitions and report the agreement and the latency and cost variability; verify a repeated case reports both (evidence: `sentinel-ai-core/eval/bench_router.py`, tests; ref: REQ-0020)

## 4. System runner

- [ ] 4.1 Implement `runner.py` replaying cases through a `TestClient` with a test session and reading the turn records by `trace_id`; verify a full case is replayed and its outcome matched (evidence: `sentinel-ai-core/eval/runner.py`, tests; ref: REQ-0025)
- [ ] 4.2 Add fault injection (Gold unavailable, expired session, tool failure) reusing the adversarial fixtures; verify each fault degrades safely and appears in the records (evidence: `sentinel-ai-core/eval/runner.py`, tests; ref: REQ-0021)
- [ ] 4.3 Include the adversarial-tagged cases in the system run and compute the unsafe-outcome rate with the full denominator; verify it matches the adversarial run convention (evidence: `sentinel-ai-core/eval/runner.py`, `evidence/adversarial/20260930T214744Z/summary.json`; ref: REQ-0021)

## 5. Report and freeze

- [ ] 5.1 Implement `report.py` writing `summary.json` and `report.md` with n, case mix, versions, variability and the failures; verify a metric without its n is rejected (evidence: `sentinel-ai-core/eval/report.py`, tests; refs: REQ-0022, REQ-0019, REQ-0024)
- [ ] 5.2 Write results write-once under `evidence/evaluation-runs/<run-id>/` and refuse to overwrite an existing run; verify a second run gets a new folder (evidence: `evidence/evaluation-runs/`; ref: REQ-0028)

## 6. Integration

- [ ] 6.1 Run the full harness offline, freeze one run and verify `summary.json` carries every mandatory metric and that no connection was opened (evidence: `evidence/evaluation-runs/<run-id>/summary.json`; ref: REQ-0055)
- [ ] 6.2 Update the requirements status for REQ-0016, REQ-0017, REQ-0019, REQ-0020, REQ-0021, REQ-0022, REQ-0024, REQ-0025, REQ-0055 and REQ-0057, and reference the run in the ML area doc (evidence: `docs/requirements/requirements.md`, `docs/build/areas/ml.md`)
