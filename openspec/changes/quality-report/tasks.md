# Tasks

Owner: Natalia. Areas: [data](../../../docs/build/areas/data.md). Decisions: [008](../../../docs/build/decisions/008-pii-gold-handling.md). Paths are under `sentinel-data-engine/` unless stated.

- [ ] 1 Generate every section of the full report (drop breakdown, quarantine per rule, orphans, late arrivals, nulls) from collectors in `src/sentinel_data/local_runner.py`. Evidence: a rerun with the default report path keeps all sections; tests over a small fixture.
- [ ] 2 Add the `verify` mode comparing figures with the committed report. Evidence: its output in the commit body and a test that a changed figure fails.
- [ ] 3 Optional: keep `duration_seconds`, `wait_time_seconds` and the `process_date` columns in Silver with quality rules; compare Silver counts before and after. Evidence: `src/sentinel_data/transforms.py`, catalog rules, counts in the commit body.
- [ ] 4 Commit the regenerated report and update REQ-0015 evidence. Evidence: `data_quality_report.md` and `docs/requirements/data-ml.md`.
