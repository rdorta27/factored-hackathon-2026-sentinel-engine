# Tasks

## 1. Script skeleton and data reading

- [ ] 1.1 Create `evidence/evaluation/eval_measure.py` with the stdlib helpers (`scan`, `in_window`, `value_counts`, `date_guard`, `record`) and the mode dispatch; verify `python3 eval_measure.py --help` lists the modes (evidence: `evidence/evaluation/eval_measure.py`; ref: `evidence/flows/measure_flow.py`)
- [ ] 1.2 Wire the data location (`BASE/data` and `dirname(BASE)/data`), the window and the held-out cut; verify the script stops with a clear message when the data is missing (evidence: `evidence/evaluation/eval_measure.py`; ref: `evidence/flows/method.md`)

## 2. Label universe and label quality

- [ ] 2.1 Compute the full `category x subcategory` counter for Claim, for Complaint and for the whole history, and persist it under `summary.json.labels`; verify the output holds every distinct combination and not a top-N slice (evidence: `evidence/evaluation/2024Q4-v1/summary.json`; refs: REQ-0016, decision 007)
- [ ] 2.2 Compute the null counts of `category` and `subcategory` and the `description`-contains-`category` check; verify the leak count matches the known value (evidence: `evidence/evaluation/2024Q4-v1/summary.json`; ref: REQ-0017)

## 3. Mix, amounts, intent and thresholds

- [ ] 3.1 Compute the Claim mix by month, country, reception channel, priority and status, plus the claimed-amount percentiles per subcategory; verify each dimension is present in `summary.json.mix` and `summary.json.amounts` (evidence: `evidence/evaluation/2024Q4-v1/summary.json`; ref: REQ-0020)
- [ ] 3.2 Compute the `contact_reason` distribution and the escalation, resolution and follow-up flags; verify every reason appears with its count and denominator (evidence: `evidence/evaluation/2024Q4-v1/summary.json`; ref: REQ-0055)
- [ ] 3.3 Compute the transaction-amount and fraud-score percentiles per country; verify the output reports them per country and currency (evidence: `evidence/evaluation/2024Q4-v1/summary.json`; refs: pending decisions 025, 026)

## 4. Freeze, verify and guard

- [ ] 4.1 Write the write-once run folder (`summary.json`, `method.md`, `MANIFEST.md`, `README.md`) with the data hashes; verify a second run creates a new folder without touching the first (evidence: `evidence/evaluation/2024Q4-v1/`; ref: REQ-0028)
- [ ] 4.2 Implement `verify` to recompute the data hashes and every summary field; verify it exits non-zero and names the field on a deliberate mismatch (evidence: `evidence/evaluation/eval_measure.py`; ref: REQ-0028)
- [ ] 4.3 Add an aggregate-only guard that rejects any output value shaped like an identifier or personal data; verify a test with a planted identifier fails the guard (evidence: `evidence/evaluation/eval_measure.py`, tests; refs: REQ-0047, REQ-0031)

## 5. Derived label set

- [ ] 5.1 Add a derivation step that writes `sentinel-ai-core/eval/labels.json` from the latest frozen run with its `run_id` and summary hash; verify the file records the provenance and changes when the run changes (evidence: `sentinel-ai-core/eval/labels.json`; refs: REQ-0016, REQ-0017)

## 6. Integration

- [ ] 6.1 Run the full script against the dataset, freeze `2024Q4-v1` and confirm `verify` passes (evidence: `evidence/evaluation/2024Q4-v1/summary.json`; ref: `evidence/flows/README.md`)
- [ ] 6.2 Update the requirements status for REQ-0016, REQ-0017 and REQ-0020 and reference the run in the ML area doc (evidence: `docs/requirements/requirements.md`, `docs/build/areas/ml.md`)
