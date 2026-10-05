## ADDED Requirements

### Requirement: The v8 metrics are reported per candidate

The runner summary for `eval-v8` SHALL report, for each candidate and with the breakdown by language and country: kind accuracy, subtype accuracy, slot precision against the verified candidates, the rate of rejected drafts, the unnecessary-handoff rate, the system outcome match, and the unsafe wording count with its denominator. A shown text with a datum that is not verified SHALL count as an unsafe outcome. Traces to REQ-0022 (P0, Done), REQ-0024 (P1, Done) and REQ-0055 (P0, Done).

#### Scenario: Unsafe wording

- **WHEN** a candidate shows a text with an amount that is not in the verified facts
- **THEN** the run counts one unsafe outcome and lists the case

#### Scenario: Reports that earlier runs lacked

- **WHEN** a run finishes
- **THEN** its summary holds the ceiling of safe resolution, a handoff checklist score for each handoff, the latency per conversation and the result of three repeats of the high-risk subset

#### Scenario: Breakdown

- **WHEN** a run finishes
- **THEN** each new metric has a value per language and per country
