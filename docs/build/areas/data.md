# Data Engineering

**Evaluation criterion:** data extraction and transformation. **Owner:** Natalia.

**Requirements:** those in the `data` area in the [requirements table](../../requirements/requirements.md).

**Related:** [dataset](../../understand/dataset.md) (tables and columns), [architecture](../../understand/architecture.md).

## Scope

- **Repeatable, deterministic ETL/ELT pipeline**: same input, same output.
- **Strict schema contracts**: invalid data is rejected or quarantined and reported; it never enters silently.
- **Quality checks**, **lineage**, and **freshness policy**.
- **Per-customer record isolation**, the basis of access control.
- Batch, incremental, or streaming processing depending on latency and freshness. Incremental files do not mandate streaming.
- With static data: labeled **refresh fixture**, without modifying the official data.
- Source inventory: real, de-identified, synthetic, or team-generated.

## Incremental processing

Large tables arrive partitioned by date, with late arrivals, duplicates, and evolving schema. Pipeline pieces:

| Piece | What it does |
|---|---|
| Watermark | Records up to which partition was processed; the next run picks up only what is new |
| Reprocessing window | Re-examines the last N days to capture late arrivals (the watermark alone would skip them) |
| Idempotent upsert | If the key exists, update; if not, insert. Reprocessing does not duplicate |
| Key-based deduplication | Absorbs the ~2% duplicates |
| Versioned contracts | Detect new columns and decide whether to accept them; never silently |
| Freshness policy | Declares the maximum acceptable lag (e.g., 24 h) |

Streaming is not mandatory: it is only worthwhile if the flow needs seconds-level freshness.

## Pipeline cases to handle

- LATAM numeric formats (e.g., "1.200,50"): the contract defines the expected format instead of guessing it.
- Currency mandatory and validated on every amount.
- Null is not orphan: the contract distinguishes them (see [dataset](../../understand/dataset.md#relationships-between-tables)).
- Date partitions: we read only new partitions plus the reprocessing window.
- Each tool read returns the data and its "updated through" mark.

## Evidence for evaluation

- [ ] Executable pipeline with a single command
- [ ] Contracts and quality report
- [ ] Passing refresh fixture
- [ ] Source inventory

## Pending decisions

- Pipeline tooling
- Batch or incremental (depends on how the data arrives)
