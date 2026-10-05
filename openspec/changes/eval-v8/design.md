---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Rules first.** The amendment is committed before the sealed set is measured, and before any v3 number on held-out cases. Its targets come from development runs of the baseline and `router_v2` on the `router-v3` development cases.
2. **Write and seal early, measure last.** The seal covers the cases, not the code. Sealing early does not use the single measurement. Measuring is the only step that waits for the freeze.
3. **Two authors, both isolated.** Each author gets only the definitions of the contract and, for the multi-turn block, the policy outcomes and the chat spec scenarios. Neither reads the prompt, the examples, the cut-offs or the amendment.
4. **Stable multi-turn outcomes.** The block holds situations whose end (a verified case number, a refusal or a handoff) is set by policy. Opener cases expect what decision 024 and the chat spec fix: a friendly reply and no handoff. A sealed case is never edited.
5. **Rehearsal on development data.** It proves the runner, the new metrics, the spend cap and the report before the one real measurement.
6. **Unsafe wording is an unsafe outcome.** A shown text with a datum that is not verified counts with the unsafe outcomes of the gates.
7. **Same settings as `eval-v7`.** GLM 5.3 Flash on both routes, reasoning low, temperature 0, same seed and cluster bootstrap. The token cap may rise for drafts and is reported.

## Risks / Trade-offs

- **Time:** authoring and review take most of the work. The multi-turn block is the first cut; the intent block alone still measures the model.
- **A sealed expectation turns out wrong:** the case stays and the report states it. The mitigation is decision 4.
- **Shared files:** `eval/metrics.py`, `runner.py` and `report.py` are also touched by `trained-baseline`. Merge `trained-baseline` and `router-v3` first.
- **Model-written cases:** the same provenance limit as `eval-v7`; stated.
