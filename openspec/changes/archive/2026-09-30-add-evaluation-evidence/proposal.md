# Proposal

## Why

The evaluation set must be labelled and stratified from the real case mix
(REQ-0016, REQ-0017, REQ-0020), but the repository freezes flow measurements
only. The category and subcategory universe of `complaints` is printed by
`measure_flow.py` and never persisted, and no artifact captures the case mix,
the intent mix or the reference thresholds the evaluation needs. Without that
evidence the classifier has no label set and the set cannot be stratified
realistically.

## What Changes

- Add a stdlib evidence script at `evidence/evaluation/eval_measure.py`,
  following the `measure_flow.py` pattern, reading the gitignored dataset.
- Extract and freeze in a write-once run `evidence/evaluation/<run-id>/summary.json`:
  the label universe (`category x subcategory` for Claim, and Complaint/global),
  the case mix (month, country, channel, priority, status), the claimed-amount
  percentiles, the label-quality checks (nulls and the `description` leak) and
  the intent mix (`contact_reason` and the escalation and resolution flags).
- Add a `verify` mode that recomputes the data hashes and every summary field,
  like the flow evidence.
- Derive `sentinel-ai-core/eval/labels.json` from the run, carrying provenance
  (run id and hash), so the evaluation runner consumes a pinned label set.
- Record the window, the held-out cut and the method in `method.md` and
  `MANIFEST.md`.

## Non-goals

- Writing evaluation cases: those are team-written (decision 007) and belong to
  the evaluation runner change.
- Extracting dataset rows: only aggregate counts and shares leave the process.
- Choosing the classifier model or prompt: decision 007 and pending decision 10.
- The flow-selection page `02-flow-measurements.md`: unchanged.

## Capabilities

### New Capabilities

- `evaluation-evidence`: freezes the label universe, the case mix and the
  reference thresholds the evaluation consumes, as reproducible aggregate
  evidence.

### Modified Capabilities

None.

## Impact

- New: `evidence/evaluation/` (script, method, manifest, frozen run) and the
  derived `sentinel-ai-core/eval/labels.json`.
- Config: the dataset is reached through the gitignored symlink
  `evidence/evaluation/data/`; no rows or secrets enter the repository.
- Requirements: REQ-0016, REQ-0017, REQ-0020; decisions 007 and 025-026.
