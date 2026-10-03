# Proposal

**Owner:** Natalia (pipeline code in `sentinel-data-engine/`).

## Why

REQ-0015 (P0) is marked Done on `sentinel-data-engine/data_quality_report.md`: volume drop (~11.5%), deduplication, quarantine, orphans, late arrivals and nulls. Those sections were written by hand on top of a file the pipeline regenerates on every run (`--report-out data_quality_report.md`, `local_runner.py` `_generate_report`). They were overwritten once (the 232-line version of `a94bca5` became 91 lines) and restored in `89ca1d4`; the next default run overwrites them again. They also cannot be regenerated or checked, while the repository's rule is that figures come from scripts. The brief asks for repeatable preparation with contracts, quality checks, lineage and a freshness policy, and the kickoff counts data quality under Data Analytics and Data Engineering.

## What Changes

- The report generator computes and writes every section the hand-written version has: per-table Bronze and Silver counts with the drop explained (deduplication, quarantine by rule, orphans), late arrivals per partitioned table, null rates for mandatory and optional fields, country normalisation, Gold eligibility and the PII guardrails.
- A `verify` mode regenerates the figures from the local DuckDB file and compares them with the committed report.
- Optional, same owner: Silver keeps `duration_seconds` and `wait_time_seconds` of `call_center_interactions`, and `process_date` of `complaints`, `call_center_interactions` and `satisfaction_surveys`, with their quality rules.

## Capabilities

### New Capabilities
- `data-quality-report`: what the generated report contains and how it is verified.

### Modified Capabilities
(none)

## Impact

- `sentinel-data-engine/src/sentinel_data/local_runner.py` (collection and report), its tests, `data_quality_report.md`, REQ-0015 evidence.
- Not changed: the Gold service view, the app.

## Non-goals

- Changing quarantine rules or deduplication logic.
- Dashboards.

## Assumptions

- Natalia owns and executes this change; no other plan depends on it except the REQ-0015 evidence and, optionally, the ROI source in `evaluation-final`.
