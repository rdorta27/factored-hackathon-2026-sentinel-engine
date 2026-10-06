## ADDED Requirements

### Requirement: A second sealed set covers openers, subtypes, slots and multi-turn resolution

A new held-out set for `2024Q4-eval-v8` SHALL be written by authors who have not seen prompt v3, its examples, its cut-offs or the 018 amendment. Its intent block SHALL hold the v7 categories, openers, status questions, out-of-scope subtypes and slot cases in the four variants, with the expected kind, subtype and slots. Its multi-turn block SHALL name the charge to select, whether to confirm and the expected end (a verified case number, a refusal or a handoff), and SHALL hold only situations whose end the policy sets. Its attack block SHALL cover marked and unmarked prompt injection, unauthorized access, expired session, bad data, tool failure and multilingual ambiguity, and its noisy twins SHALL copy cases of the intent block with small changes. The set SHALL be reviewed and back-translated as in v7, and SHALL be sealed under a new hash before the measurement. A top-up block SHALL add at least 6 bases for each intent with fewer than 10 bases, and SHALL be sealed under its own hash. The v7 entry of `measured.json` SHALL stay unchanged. Traces to REQ-0017 (P0, Done), REQ-0020 (P0, Done), REQ-0012 (P0, Done) and REQ-0055 (P0, Done); decision 018.

#### Scenario: Openers and slots are in the set

- **WHEN** the new set is counted
- **THEN** it holds opener, status, out-of-scope subtype and slot cases in each variant

#### Scenario: Attacks and noisy twins are in the set

- **WHEN** the new set is counted
- **THEN** it holds an attack block and a set of noisy twins, so the gate D7 can be read on it

#### Scenario: The authors were isolated

- **WHEN** the provenance of the set is read
- **THEN** it states that no author could read the prompt, the examples, the cut-offs or the amendment

#### Scenario: Sealing does not use the measurement

- **WHEN** the set is sealed
- **THEN** `measured.json` has no entry for the new hash

#### Scenario: Thin intents get a top-up

- **WHEN** an intent has fewer than 10 bases after the v8 seal
- **THEN** the top-up block adds at least 6 bases for it before the freeze
