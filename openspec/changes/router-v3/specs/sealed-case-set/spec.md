## ADDED Requirements

### Requirement: A second sealed set covers openers

A new held-out set for `2024Q4-eval-v8` SHALL be written by an author who has not seen prompt v3, its examples or the 018 amendment, SHALL include the opener and small-talk categories and the v7 categories in the four variants, SHALL be reviewed and back-translated as in v7, and SHALL be sealed under a new hash before any v3 call on it. The hash SHALL be appended to `measured.json` after its single measurement; the v7 entry SHALL stay unchanged. Traces to REQ-0017 (P0, In progress), REQ-0020 (P0, Done) and REQ-0012 (P0, Done); decision 018.

#### Scenario: Openers are in the set

- **WHEN** the new set is counted
- **THEN** it holds greeting, courtesy, small-talk and greeting-with-request cases in each variant

#### Scenario: The author was isolated

- **WHEN** the provenance of the set is read
- **THEN** it states that the author could not read the prompt, the examples or the amendment

#### Scenario: Measured once

- **WHEN** a second measurement of the new hash is attempted
- **THEN** the runner refuses it
