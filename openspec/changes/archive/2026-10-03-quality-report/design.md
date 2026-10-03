# Design

## Context

`LocalPipelineRunner` collects Bronze, Silver and Gold counts and quality metrics (`_collect_*`, `local_runner.py`) and writes the report in `_generate_report`, which today emits only volume summary, country normalisation, Gold eligibility and PII sections. The full version in `a94bca5` added the drop breakdown, quarantine, orphans, late arrivals and nulls by hand. Quarantined rows go to `rejected_records`. Read-only checks on 2026-10-02: 14% of call-center interactions have no duration in Bronze; a fresh run reproduced every Silver and Gold count.

## Decisions

1. **Move the hand-written sections into collectors** that query the DuckDB file (counts per rule from `rejected_records`, orphans by anti-join, late arrivals as `process_date` after the event date, nulls per column), and render them in `_generate_report`.
2. **`verify` compares figures, not text,** so wording can change without failing.
3. **Silver columns are optional in the same change** because they share the pipeline run; they come with quality rules for the new columns, and a before-and-after Silver count check.

## Risks / Trade-offs

- **Run time:** extra queries over 4.4 million rows add seconds, not minutes.
- **New rules quarantining rows by mistake** (as the old `fraud_score` range could): compare Silver counts before and after.
