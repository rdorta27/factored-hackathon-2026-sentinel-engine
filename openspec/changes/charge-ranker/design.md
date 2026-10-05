---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Rules first.** Decision 025 fixes the metrics, the splits, the threshold rule and the serving rule before any model is trained. The commit order is the proof.
2. **Labels from real data.** The label of an example is the transaction id that the description was built from. The description text is ours. The labels are exact.
3. **One example, many candidates.** For one customer and one day, the candidates are that customer's recent charges, as `lookup_transactions` would list them. The other charges of the same customer are the hard negatives.
4. **Clues share code with the rules.** The clues call the parsers of `app/ai/grounding.py`. The selector adds weights and does not replace the parsers. `rules_fixed` is the same parsers with fixed order.
5. **Three splits at once.** By customer (a hash of the customer id gives 60% train, 20% validation, 20% test), and by time (train before 2025-01-01, validation from 2025-01-01 to 2025-06-30, test from 2025-07-01). A test customer is later and unseen. The test set is measured once.
6. **Calibration and threshold.** Calibrate the scores on train only. Set the picking threshold on validation only, so that the share of wrong automatic picks is 1% or less.
7. **No gaps in the story.** Many charges have no merchant name (77% in the development zone). The report splits results by "the charge has a merchant name" and by language.
8. **Lock by hash.** The run stores the hash of the model file, the seed, the family list and the threshold. A test fails if the evaluation module imports the training module.
9. **One seam.** The selector plugs in behind `narrow(...)` of `chat-start`. It changes no line of `step.py`.
10. **Serving is decided before the freeze.** `eval-v8` measures the served configuration. The switch can turn on only before the code freeze; after it, the selector stays off, so v8 describes what the demo serves.
11. **Where the model file lives.** In the run folder, with weights only.

## Risks / Trade-offs

- **Our phrasing is not the phrasing of customers.** A test family never seen in training reduces the risk, and the report says it plainly.
- **Time.** About half a day. If the run is not frozen before the code freeze, it ships as an experiment and the service does not use it.
- **Overlap with `chat-start`.** That change improves the parsers. The final comparison waits for it, so that the rules are at their best.
- **Privacy.** Training reads raw transactions on this machine only. Nothing with rows goes to git.
