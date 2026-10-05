---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Same method as the earlier runs.** One script with modes, data hashes in a manifest, and a `verify` mode that checks the hashes. The script reads the raw CSV files of the data engine in place and copies nothing.
2. **Development zone only.** This keeps one rule for all evidence: nothing from 2025-07-01 onward is read to support a choice.
3. **The mapping comes first.** A table maps each value of `contact_reason` and `reason_category` to a candidate workflow (account or payment inquiry, card support, transaction dispute, credit information, other). It is written and committed before the first number. The product field is empty on about 60% of calls ([008](../../../docs/build/decisions/008-account-inquiry-scope.md)), so the mapping does not use it.
4. **First contact means the dataset field.** A call "solved at the first contact" is a call with `was_resolved` true. The README says so, and says that the dataset does not tell if the customer called again.
5. **Handling time is partial.** Some calls have no duration. The run reports how many, and averages only the calls that have one. It does not fill the gaps.
6. **Ranges.** A 95% range for each rate (Wilson). A 95% range for the busy-day level and the highest day (resample the days).
7. **Plain words.** The README and the rationale page define each term once: first-contact resolution, busy-day level, agent hours, 95% range.

## Risks / Trade-offs

- **The dataset is synthetic.** The numbers describe the dataset, not a real bank. The page says so.
- **The mapping is a judgment.** A different mapping can change the ranking. The run reports the ranking under the mapping that was committed first, and lists the reasons that map to "other".
- **Transcripts are templates.** The run does not use them.
