---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ml](../../../docs/build/areas/ml.md). Decisions: [016](../../../docs/build/decisions/016-router-models.md), [017](../../../docs/build/decisions/017-portuguese.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md), [024](../../../docs/build/decisions/024-model-wording.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

Depends on `router-v3` (contract v3: task 1.1; development cases: task 2.1), `trained-baseline` (a candidate), the closed `chat-start` spec, and the code freeze for task 5.1 only.

## 1. Rules first

- [ ] 1.1 Run the baseline and `router_v2` on the development cases of `router-v3` (new live calls only; cap USD 1) and write the development numbers. Evidence: a development run under `evidence/evaluation-runs/`.
- [ ] 1.2 Extend the 018 amendment of `router-confidence`: unnecessary-handoff rate, system outcome match, subtype accuracy, slot precision, rejected-draft rate, unsafe wording, the v7 gates, targets from 1.1, and the v8 spend cap. Commit it before the seal. Evidence: the decision file and its commit order.
- [x] 1.3 Add the new metrics to the runner and the report, with a test per metric. Evidence: `eval/metrics.py`, `eval/report.py`, tests.
- [x] 1.4 Add three reports: the ceiling of safe resolution, a handoff checklist score (request, verified facts, actions, evidence with rule id and trace id, open questions, reason, language and country: seven items, scored by a script), and latency per conversation. Add the three repeats of the high-risk subset to the runner. Evidence: `eval/metrics.py`, `eval/report.py`, tests.

## 2. Sealed set

- [ ] 2.1 An isolated author writes the intent block, in four variants, from the definitions of the contract only. Evidence: `eval/cases/` and provenance in `eval/review/`.
- [ ] 2.2 An isolated author writes the multi-turn block from the policy outcomes and the chat spec scenarios only. Evidence: the same.
- [ ] 2.5 An isolated author writes the attack block and the noisy twins in four variants, from the attack categories of the adversarial suite and the label definitions only. Evidence: `eval/cases/` and provenance in `eval/review/`.
- [ ] 2.3 Review and back-translate all four blocks as in `eval-v7`; fix or drop drifting cases before the seal. Evidence: `eval/review/` notes.
- [ ] 2.4 Seal the set under a new hash, leaving the v7 entry unchanged. Evidence: `eval/cases/seal.json` and a test that the v7 hash is unchanged.

## 3. Rehearsal

- [ ] 3.1 Run every candidate on development data with the new metrics, the report and the spend cap; no sealed case is read. Evidence: a rehearsal run and a note of its cost and time.

## 4. Freeze gate

- [ ] 4.1 Confirm with the owner that the code is frozen: `flow-fixes`, `chat-start`, `bank-ui`, `trained-baseline`, `robustness-evidence` (code) and `router-v3` are merged. Evidence: `git log` and the owner's confirmation in the session.

## 5. Measure and judge (after the code freeze)

- [ ] 5.1 Measure once as `2024Q4-eval-v8`, with the three repeats of the high-risk subset, record the measured commit, and freeze the run. Evidence: `evidence/evaluation-runs/2024Q4-eval-v8/summary.json` and `eval/measured.json`.
- [ ] 5.2 Judge each candidate by the amendment, write the verdict, and serve v3 by default only if it passes every gate. Evidence: the result section of the amendment and `app/ai/serving.py` tests.
- [ ] 5.3 Regenerate the metrics report, update the README limits, REQ-0016 evidence and the evidence index, and add v8 to the CI replay list if it verifies offline. Evidence: those files.
