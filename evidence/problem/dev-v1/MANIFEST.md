# Data manifest — problem evidence, development zone

Generated 2026-10-05 with script `2026-10-05+problem-dev-v1`. Data is read in
place from the data engine's raw CSVs (`sentinel-data-engine/data/raw/`,
gitignored) and never copied into this folder.

Only partitions with `process_date < 2025-07-01` are listed and read. Nothing
at or after the held-out cut was downloaded for this run. The 2025-06-30
partition holds rows dated 2025-07-01 (the synthetic one-day offset); the
script reads them, excludes them and counts them
(`totals.excluded_heldout`).

## Verify

```bash
# from this folder; SENTINEL_RAW_DIR is optional when the raw data sits at
# <repo>/sentinel-data-engine/data/raw
SENTINEL_RAW_DIR=/abs/path/to/sentinel-data-engine/data/raw \
  python3 measure_problem.py verify   # every line must print OK
```

Rows are CSV records (`csv.DictReader`, utf-8-sig); the hash is sha256 over
the file bytes in sorted path order, first 16 hex characters.

| Files | Rows | sha256[:16] | Pattern (under raw/) |
|---|---|---|---|
| 198 | 123,545 | a6c56e6ade2d6928 | call_center_interactions/year=2023/month=*/day=*/*.csv |
| 366 | 228,210 | aad05095cd3ad458 | call_center_interactions/year=2024/month=*/day=*/*.csv |
| 31 | 19,496 | 1a1fb7ba78282e99 | call_center_interactions/year=2025/month=01/day=*/*.csv |
| 28 | 17,211 | 80048537fbf84724 | call_center_interactions/year=2025/month=02/day=*/*.csv |
| 31 | 19,498 | e2eed7b9a50ad5ea | call_center_interactions/year=2025/month=03/day=*/*.csv |
| 30 | 19,177 | 5fd4020eae83bebd | call_center_interactions/year=2025/month=04/day=*/*.csv |
| 31 | 19,634 | 019ec566b5f9f74a | call_center_interactions/year=2025/month=05/day=*/*.csv |
| 30 | 18,237 | 1f7a9a7030db8226 | call_center_interactions/year=2025/month=06/day=*/*.csv |

Partition totals are 465,008 calls. The event-date filter
`[2023-06-17, 2025-07-01)` keeps `totals.calls`; the difference is
`totals.excluded_heldout`. The `summary.json` of this run has sha256
`8ca15aa611153c33` (first 16 hex characters).

## Method

- **Engine.** DuckDB (a dependency of `sentinel-data-engine` and
  `sentinel-ai-core`), in memory. Columns are read as text, trimmed and cast
  (`timestamp` for `interaction_date`, `double` for `duration_seconds`).
- **Window.** The whole development zone on event dates
  (`interaction_date`), `[2023-06-17, 2025-07-01)`. Only partitions with
  `process_date < 2025-07-01` are globbed. Every row is then filtered on its
  event date; rows at or after the cut are counted, not read into any measure.
- **Mapping.** Fixed in code (`REASON_TO_WORKFLOW`) and in `README.md`, and
  committed before the first number. `contact_reason` and `reason_category`
  hold the same value on every row.
- **1. First-contact resolution.** Per reason: `n`, `resolved`
  (`was_resolved = 'true'`), the share and a Wilson 95% range in percent.
- **2. Calls per day.** Per workflow: the daily counts over the 745 days of
  the window, then the mean, the 95th percentile (the busy-day level) and the
  maximum. The 95% ranges of the last two come from a bootstrap over the days
  (2,000 resamples, seed fixed in code). A day with no call for a workflow
  counts as zero.
- **3. Agent hours.** Per workflow: calls times the mean handling time
  (`duration_seconds`, over the calls that have one) divided by the number of
  months. Months are days / 30.4375. Candidate workflows are ranked by the
  unrounded hours; `other` is a residual and is not ranked. Calls without a
  duration are counted and are not filled.
- **4. Missing values.** Per field in `FIELDS_USED`: the count and share of
  blank values, with a Wilson 95% range.
- Thresholds and constants are fixed in the script. The mapping was committed
  before the run, so the ranking cannot follow the result.
