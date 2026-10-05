---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ml](../../../docs/build/areas/ml.md). Decisions: [016](../../../docs/build/decisions/016-router-models.md), [017](../../../docs/build/decisions/017-portuguese.md), [018](../../../docs/build/decisions/018-evaluation-acceptance.md), [024](../../../docs/build/decisions/024-model-wording.md). Paths are under `sentinel-ai-core/` unless stated. Run `python3 -m pytest -q` after each group.

Depends on `router-v3` (contract v3: task 1.1; development cases: task 2.1), `trained-baseline` (a candidate), the closed `chat-start` spec, and nothing after the code freeze. The freeze gate, the single measurement, the verdict and the final report moved to `post-freeze` (tasks 1.1, 2.1, 2.2 and 2.4 there).

## 1. Rules first

- [x] 1.1 Run the baseline and `router_v2` on the development cases of `router-v3` (new live calls only; cap USD 1) and write the development numbers. Evidence: a development run under `evidence/evaluation-runs/`.
- [x] 1.2 Extend the 018 amendment of `router-confidence`: unnecessary-handoff rate, system outcome match, subtype accuracy, slot precision, rejected-draft rate, unsafe wording, the v7 gates, targets from 1.1, and the v8 spend cap. Commit it before the seal. Evidence: the decision file and its commit order.
- [x] 1.3 Add the new metrics to the runner and the report, with a test per metric. Evidence: `eval/metrics.py`, `eval/report.py`, tests.
- [x] 1.4 Add three reports: the ceiling of safe resolution, a handoff checklist score (request, verified facts, actions, evidence with rule id and trace id, open questions, reason, language and country: seven items, scored by a script), and latency per conversation. Add the three repeats of the high-risk subset to the runner. Evidence: `eval/metrics.py`, `eval/report.py`, tests.

## 2. Sealed set

- [x] 2.1 An isolated author writes the intent block, in four variants, from the definitions of the contract only. Evidence: `eval/cases/` and provenance in `eval/review/`.
- [x] 2.2 An isolated author writes the multi-turn block from the policy outcomes and the chat spec scenarios only. Evidence: the same.
- [x] 2.5 An isolated author writes the attack block and the noisy twins in four variants, from the attack categories of the adversarial suite and the label definitions only. Evidence: `eval/cases/` and provenance in `eval/review/`.
- [x] 2.3 Review and back-translate all four blocks as in `eval-v7`; fix or drop drifting cases before the seal. Evidence: `eval/review/` notes.
- [x] 2.4 Seal the set under a new hash, leaving the v7 entry unchanged. Evidence: `eval/cases/seal.json` and a test that the v7 hash is unchanged.
- [x] 2.6 An isolated author writes the top-up block in four variants: at least 6 new bases for each intent with fewer than 10 bases (`out_of_scope`, `person`, `status`), plus ambiguous messages, mixed Spanish and Portuguese, and two intents in one message. The author reads only the contract definitions. Evidence: `eval/cases/sealed_v8b/` and provenance in `eval/review/`.
- [x] 2.7 Review and back-translate the top-up block as in task 2.3; drop near copies of an earlier base and count them. Evidence: `eval/review/` notes.
- [x] 2.8 Seal the top-up block under its own hash; leave the v7 and v8 entries unchanged. Evidence: `eval/cases/sealed_v8b/seal.json` and a test that the other hashes are unchanged.

## 3. Rehearsal

- [ ] 3.1 Run every candidate on development data with the new metrics, the report and the spend cap; no sealed case is read. Evidence: a rehearsal run and a note of its cost and time.
- [ ] 3.2 Run a prompt ablation on development data with the same model and cap: no examples, 4 examples, 8 examples and the v3 prompt, on the same cases. Report accuracy, subtype accuracy, cost and latency for each. The ablation picks nothing; the gates of the amendment decide. Evidence: a development run under `evidence/evaluation-runs/` and a section in `eval/review/rehearsal-v8.md`.

## Moved to `post-freeze`

The freeze gate (old 4.1), the single measurement (5.1), the verdict (5.2) and the final report (5.3) now live in the `post-freeze` change. This plan closes when the seal, the top-up block and the rehearsal are done.
