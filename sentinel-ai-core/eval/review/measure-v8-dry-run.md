---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05

# Dry run of the v8 measurement command

Task 1.3 of `eval-v8-measure` runs `eval/measure_v8.py` on development data only.
The run reads no sealed case and leaves `eval/measured.json` unchanged.
This dry run replays the committed recordings of `2024Q4-rehearsal-v8`.
The worktree holds no model key, so the run makes no live call.
The live path is covered by `tests/test_eval_measure_v8.py`.

Cases: 198 development. Cap USD 0.45. Spend USD 0.0 (replay).

Compared metrics: 66 equal, 0 different.

| Candidate | Metric | Rehearsal v8 | Dry run | Equal |
|---|---|---|---|---|
| baseline | n | 198 | 198 | yes |
| baseline | kind accuracy | 0.5909 | 0.5909 | yes |
| baseline | kind confusion | {'charge': {'charge': 75, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'missing': {'charge': 40, 'missing': 0, 'out_of_scope': 0, 'person': 2, 'status': 0}, 'out_of_scope': {'charge': 17, 'missing': 0, 'out_of_scope': 24, 'person': 5, 'status': 0}, 'person': {'charge': 13, 'missing': 0, 'out_of_scope': 0, 'person': 18, 'status': 0}, 'status': {'charge': 4, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 0}} | {'charge': {'charge': 75, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'missing': {'charge': 40, 'missing': 0, 'out_of_scope': 0, 'person': 2, 'status': 0}, 'out_of_scope': {'charge': 17, 'missing': 0, 'out_of_scope': 24, 'person': 5, 'status': 0}, 'person': {'charge': 13, 'missing': 0, 'out_of_scope': 0, 'person': 18, 'status': 0}, 'status': {'charge': 4, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 0}} | yes |
| baseline | subtype accuracy | 0.0 | 0.0 | yes |
| baseline | subtype n | 40 | 40 | yes |
| baseline | slot precision | not defined | not defined | yes |
| baseline | slots returned | 0 | 0 | yes |
| baseline | drafts returned | 0 | 0 | yes |
| baseline | drafts rejected | 0 | 0 | yes |
| baseline | unsafe wording | 0/0 | 0/0 | yes |
| baseline | cost USD | 0.0 | 0.0 | yes |
| trained_baseline | n | 198 | 198 | yes |
| trained_baseline | kind accuracy | 1.0 | 1.0 | yes |
| trained_baseline | kind confusion | {'charge': {'charge': 75, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 42, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 0, 'out_of_scope': 46, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 4}} | {'charge': {'charge': 75, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 42, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 0, 'out_of_scope': 46, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 4}} | yes |
| trained_baseline | subtype accuracy | 0.0 | 0.0 | yes |
| trained_baseline | subtype n | 40 | 40 | yes |
| trained_baseline | slot precision | not defined | not defined | yes |
| trained_baseline | slots returned | 0 | 0 | yes |
| trained_baseline | drafts returned | 0 | 0 | yes |
| trained_baseline | drafts rejected | 0 | 0 | yes |
| trained_baseline | unsafe wording | 0/0 | 0/0 | yes |
| trained_baseline | cost USD | 0.0 | 0.0 | yes |
| router_v2 | n | 198 | 198 | yes |
| router_v2 | kind accuracy | 0.8182 | 0.8182 | yes |
| router_v2 | kind confusion | {'charge': {'charge': 68, 'missing': 5, 'out_of_scope': 2, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 25, 'out_of_scope': 16, 'person': 1, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 8, 'out_of_scope': 38, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 4, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 0}} | {'charge': {'charge': 68, 'missing': 5, 'out_of_scope': 2, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 25, 'out_of_scope': 16, 'person': 1, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 8, 'out_of_scope': 38, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 4, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 0}} | yes |
| router_v2 | subtype accuracy | 0.0 | 0.0 | yes |
| router_v2 | subtype n | 40 | 40 | yes |
| router_v2 | slot precision | 0.0588 | 0.0588 | yes |
| router_v2 | slots returned | 17 | 17 | yes |
| router_v2 | drafts returned | 0 | 0 | yes |
| router_v2 | drafts rejected | 0 | 0 | yes |
| router_v2 | unsafe wording | 0/0 | 0/0 | yes |
| router_v2 | cost USD | 0.026234 | 0.026234 | yes |
| router_v2_cutoffs | n | 198 | 198 | yes |
| router_v2_cutoffs | kind accuracy | 0.8384 | 0.8384 | yes |
| router_v2_cutoffs | kind confusion | {'charge': {'charge': 66, 'missing': 8, 'out_of_scope': 1, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 31, 'out_of_scope': 10, 'person': 1, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 8, 'out_of_scope': 38, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 0, 'missing': 4, 'out_of_scope': 0, 'person': 0, 'status': 0}} | {'charge': {'charge': 66, 'missing': 8, 'out_of_scope': 1, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 31, 'out_of_scope': 10, 'person': 1, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 8, 'out_of_scope': 38, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 0, 'missing': 4, 'out_of_scope': 0, 'person': 0, 'status': 0}} | yes |
| router_v2_cutoffs | subtype accuracy | 0.0 | 0.0 | yes |
| router_v2_cutoffs | subtype n | 40 | 40 | yes |
| router_v2_cutoffs | slot precision | 0.0588 | 0.0588 | yes |
| router_v2_cutoffs | slots returned | 17 | 17 | yes |
| router_v2_cutoffs | drafts returned | 0 | 0 | yes |
| router_v2_cutoffs | drafts rejected | 0 | 0 | yes |
| router_v2_cutoffs | unsafe wording | 0/0 | 0/0 | yes |
| router_v2_cutoffs | cost USD | 0.026234 | 0.026234 | yes |
| router_v3 | n | 198 | 198 | yes |
| router_v3 | kind accuracy | 0.9899 | 0.9899 | yes |
| router_v3 | kind confusion | {'charge': {'charge': 73, 'missing': 2, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 42, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 0, 'out_of_scope': 46, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 4}} | {'charge': {'charge': 73, 'missing': 2, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 42, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 0, 'out_of_scope': 46, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 0, 'status': 4}} | yes |
| router_v3 | subtype accuracy | 1.0 | 1.0 | yes |
| router_v3 | subtype n | 40 | 40 | yes |
| router_v3 | slot precision | 0.1395 | 0.1395 | yes |
| router_v3 | slots returned | 129 | 129 | yes |
| router_v3 | drafts returned | 94 | 94 | yes |
| router_v3 | drafts rejected | 0 | 0 | yes |
| router_v3 | unsafe wording | 0/94 | 0/94 | yes |
| router_v3 | cost USD | 0.119472 | 0.119472 | yes |
| router_v3_cutoffs | n | 198 | 198 | yes |
| router_v3_cutoffs | kind accuracy | 0.5404 | 0.5404 | yes |
| router_v3_cutoffs | kind confusion | {'charge': {'charge': 27, 'missing': 48, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 42, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 39, 'out_of_scope': 7, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 0, 'missing': 4, 'out_of_scope': 0, 'person': 0, 'status': 0}} | {'charge': {'charge': 27, 'missing': 48, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'missing': {'charge': 0, 'missing': 42, 'out_of_scope': 0, 'person': 0, 'status': 0}, 'out_of_scope': {'charge': 0, 'missing': 39, 'out_of_scope': 7, 'person': 0, 'status': 0}, 'person': {'charge': 0, 'missing': 0, 'out_of_scope': 0, 'person': 31, 'status': 0}, 'status': {'charge': 0, 'missing': 4, 'out_of_scope': 0, 'person': 0, 'status': 0}} | yes |
| router_v3_cutoffs | subtype accuracy | 1.0 | 1.0 | yes |
| router_v3_cutoffs | subtype n | 40 | 40 | yes |
| router_v3_cutoffs | slot precision | 0.1395 | 0.1395 | yes |
| router_v3_cutoffs | slots returned | 129 | 129 | yes |
| router_v3_cutoffs | drafts returned | 94 | 94 | yes |
| router_v3_cutoffs | drafts rejected | 0 | 0 | yes |
| router_v3_cutoffs | unsafe wording | 0/94 | 0/94 | yes |
| router_v3_cutoffs | cost USD | 0.119472 | 0.119472 | yes |

## Latency

The rehearsal measured the wall-clock of each call. The first pass over a recorder ran live,
so it reports the live time. The second pass read the recording and reports the read time.
The measurement restores the recorded live latency for every pass, so the cut-off variant
reports the same latency as its prompt. This is the intended difference, not a metric difference.

| Candidate | Metric | Rehearsal v8 | Dry run |
|---|---|---|---|
| baseline | latency p50 ms | 0.01 | 0.01 |
| baseline | latency p95 ms | 0.01 | 0.01 |
| trained_baseline | latency p50 ms | 0.12 | 0.12 |
| trained_baseline | latency p95 ms | 0.23 | 0.2 |
| router_v2 | latency p50 ms | 1174.52 | 1181.15 |
| router_v2 | latency p95 ms | 3425.51 | 3424.25 |
| router_v2_cutoffs | latency p50 ms | 0.25 | 1181.15 |
| router_v2_cutoffs | latency p95 ms | 0.44 | 3424.25 |
| router_v3 | latency p50 ms | 2152.81 | 2154.85 |
| router_v3 | latency p95 ms | 4913.34 | 4910.76 |
| router_v3_cutoffs | latency p50 ms | 0.54 | 2154.85 |
| router_v3_cutoffs | latency p95 ms | 1.07 | 4910.76 |

## Result

Every non-latency metric of the six candidates equals the rehearsal.

The command refuses a second measurement, refuses a modified seal, stops at the cap
without freezing and leaves `eval/measured.json` unchanged on a failure.
The tests in `tests/test_eval_measure_v8.py` prove these four guards.
