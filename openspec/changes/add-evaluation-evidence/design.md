# Design

## Context

See proposal.md for motivation. Current state that shapes the approach:

- `evidence/flows/` is the working pattern: a stdlib `measure_flow.py`, a frozen
  run folder with `summary.json`, `method.md` and `MANIFEST.md`, a `verify` mode
  that recomputes hashes, and a renderer that reads the latest run.
- `measure_flow.py` prints `value_counts(claim, "category", "subcategory")` but
  never persists it, so the label universe is measured and lost.
- The dataset lives in a gitignored `data/` tree of CSV files; the flow script
  reads `BASE/data` (root) or `dirname(BASE)/data` (run copies).
- The evaluation runner is a separate change and consumes a pinned label set.

## Goals / Non-Goals

**Goals:**
- One reproducible script that freezes the label universe, case mix, intent mix
  and reference thresholds as aggregate evidence.
- A derived label set the evaluation runner consumes with provenance.
- The same write-once and verify guarantees as the flow evidence.

**Non-Goals:**
- Writing evaluation cases, running the system, or computing metrics.
- A rendered docs page: the summary is read by the runner, not embedded in the
  flow-selection page.
- Reading the held-out zone or any dataset rows out of the process.

## Decisions

### Decision: stdlib and CSV, mirroring `measure_flow.py`

The script uses only the standard library and reads the CSV tree directly, as the
flow evidence does. This keeps `evidence/` self-contained and reproducible with
no lockfile. Alternatives: DuckDB or pandas (rejected: they add a dependency and
break the evidence convention). If the dataset is later served as Parquet, only
the reader helper changes.

### Decision: a new `evidence/evaluation/` home, not a flows run

The artifact answers "how do we evaluate", not "which flow to build", and its
consumer is the runner. It gets its own folder, script, `method.md` and
`MANIFEST.md`, and does not touch `evidence/flows/` or the generated page.

### Decision: one summary, grouped by concern

`summary.json` is grouped as `meta`, `labels`, `mix`, `amounts`,
`label_quality`, `intent_mix` and `thresholds`, so each consumer reads only its
section and the `verify` mode can compare field by field.

### Decision: window-scoped run id

Runs are named by window and version (`2024Q4-v1`), like the flow runs, so the
same window can be re-measured as a new version without editing an earlier run.
A run writes `summary.json`, `method.md`, `MANIFEST.md` and a `README.md`.

### Decision: explicit derivation of the label set

A small step reads the latest frozen run and writes
`sentinel-ai-core/eval/labels.json` with provenance (`run_id` and a hash of
`summary.json`). Derivation is an explicit command, not a side effect of a run,
so the runner never silently picks up a changed label set.

### Decision: verify recomputes hashes and fields

`verify` recomputes the data hashes against `MANIFEST.md` and re-derives every
summary field, failing on any mismatch, exactly as the flow evidence does. This
is what makes a re-synced dataset visible instead of silently changing labels.

### Decision: aggregates only, guarded

The script builds counts, shares and percentile values and never emits a row. A
check rejects any output value that looks like an identifier, and `MANIFEST.md`
holds data hashes, not data.

## Risks / Trade-offs

- [Dataset not in the repository] → the script reads a gitignored `data/`
  symlink; without it the run stops with a clear message.
- [A re-synced dataset changes the labels] → `verify` fails on a hash or value
  mismatch; a new run is a new folder.
- [Held-out contamination] → the window and the held-out cut are enforced in
  code, and the held-out row count is reported.
- [Personal data in an aggregate] → only counts and percentiles are written, and
  a guard rejects identifier-shaped values.
- [Slow scan on large tables] → the window slices are small (tens to hundreds of
  thousands of rows); stdlib CSV stays within seconds.

## Migration Plan

Additive and offline. No service code changes; nothing runs until the script is
invoked against the data. Rollback is deleting the derived label set; the frozen
run stays as evidence.

## Open Questions

- The exact run-id scheme if the window ever changes (keep `2024Q4-vN` for now).
- Whether the thresholds section should also cover cards, or charges only.
