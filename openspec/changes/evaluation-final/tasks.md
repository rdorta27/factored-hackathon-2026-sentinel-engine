# Tasks

Areas: [analysis](../../../docs/build/areas/analysis.md#country-monitoring), [ml](../../../docs/build/areas/ml.md). Decisions: [018](../../../docs/build/decisions/018-evaluation-acceptance.md), [013](../../../docs/build/decisions/013-experiment-tracking.md). Rebase on `resolution-eval` first. Paths are under `sentinel-ai-core/` unless stated.

## 1. Breakdown and monitoring code

- [ ] 1.1 Group `system_metrics` by variant and by country with n, intervals by situation, descriptive label and "not defined"; carry it into new summaries and reports. Evidence: `tests/test_eval_metrics.py` and `tests/test_eval_report.py` with invented turns whose groups add up; no file of a frozen run changes.
- [ ] 1.2 Monitor script over a turn log: per country and language, aggregates only, write-once, workload stated, unknown country apart. Evidence: a test over invented records with no trace id or text in the output, and an existing run id refused.

## 2. Final measurement (after chat-loop)

- [ ] 2.1 Freeze `2024Q4-resolution-v2` with the committed rules, recordings under the spend cap, records to a temporary var directory; verify offline. Evidence: `evidence/evaluation-runs/2024Q4-resolution-v2/summary.json` and the `verify` output in the commit body.
- [ ] 2.2 Freeze the monitoring evidence from that log. Evidence: `evidence/monitoring/<run-id>/summary.json`.

## 3. ROI

- [ ] 3.1 Script for the call-center aggregates (Silver if it has the durations, else Bronze), write-once with `verify`. Evidence: `evidence/roi/<run-id>/summary.json` and a test over a temporary DuckDB file.
- [ ] 3.2 Write `docs/build/roi.md`: labelled inputs, formula, sensitivity table over the assumed hour range, the v2 rate beside it, the headroom finding, what is not claimed; point `docs/build/metrics.md` to it. Evidence: those files.

## 4. Report and requirements

- [ ] 4.1 Final `docs/build/metrics-report.md`: section 6 on resolution-v2 with v1 beside it, a breakdown section with the segment limit, the monitoring result, ROI link; analysis area updated. Evidence: those files.
- [ ] 4.2 Requirements: REQ-0055 and REQ-0017 to Done with evidence; REQ-0024 and REQ-0050 cite the system evidence next to the dataset reports and move to Done; REQ-0057 to Done as a projection; README results; task 7 in `team/tasks.md`. Evidence: `docs/requirements/` and those files.
