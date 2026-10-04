## ADDED Requirements

### Requirement: A second sealed set covers openers, subtypes, slots and multi-turn resolution

A new held-out set for `2024Q4-eval-v8` SHALL be written by authors who have not seen prompt v3, its examples, its cut-offs or the 018 amendment. Its intent block SHALL hold the v7 categories, openers, status questions, out-of-scope subtypes and slot cases in the four variants, with the expected kind, subtype and slots. Its multi-turn block SHALL name the charge to select, whether to confirm and the expected end (a verified case number, a refusal or a handoff), and SHALL hold only situations whose end the policy sets. The set SHALL be reviewed and back-translated as in v7, and SHALL be sealed under a new hash before the measurement. The v7 entry of `measured.json` SHALL stay unchanged. Traces to REQ-0017 (P0, Done), REQ-0020 (P0, Done), REQ-0012 (P0, Done) and REQ-0055 (P0, Done); decision 018.

#### Scenario: Openers and slots are in the set

- **WHEN** the new set is counted
- **THEN** it holds opener, status, out-of-scope subtype and slot cases in each variant

#### Scenario: The authors were isolated

- **WHEN** the provenance of the set is read
- **THEN** it states that no author could read the prompt, the examples, the cut-offs or the amendment

#### Scenario: Sealing does not use the measurement

- **WHEN** the set is sealed
- **THEN** `measured.json` has no entry for the new hash

#### Scenario: Measured once

- **WHEN** a second measurement of the new hash is attempted
- **THEN** the runner refuses it
