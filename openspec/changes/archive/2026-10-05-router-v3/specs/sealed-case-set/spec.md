## ADDED Requirements

### Requirement: A second sealed set covers openers, subtypes and slots

A new held-out set for `2024Q4-eval-v8` SHALL be written by an author who has not seen prompt v3, its examples or the 018 amendment. Its intent block SHALL hold the v7 categories, openers, status questions, out-of-scope subtypes and slot cases in the four variants, with the expected kind, subtype and slots. Its multi-turn block SHALL name the charge to select, whether to confirm and the expected end (a verified case number, a refusal or a handoff). The set SHALL be reviewed and back-translated as in v7, and SHALL be sealed under a new hash before any v3 call on it. The v7 entry of `measured.json` SHALL stay unchanged. Traces to REQ-0017 (P0, Done), REQ-0020 (P0, Done), REQ-0012 (P0, Done) and REQ-0055 (P0, Done); decision 018.

#### Scenario: Openers and slots are in the set

- **WHEN** the new set is counted
- **THEN** it holds opener, status, out-of-scope subtype and slot cases in each variant

#### Scenario: The author was isolated

- **WHEN** the provenance of the set is read
- **THEN** it states that the author could not read the prompt, the examples or the amendment

#### Scenario: Measured once

- **WHEN** a second measurement of the new hash is attempted
- **THEN** the runner refuses it
