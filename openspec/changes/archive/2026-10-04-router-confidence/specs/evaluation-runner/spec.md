## ADDED Requirements

### Requirement: Cut-offs are fitted on development and chosen on validation

The case set SHALL gain a `validation` split carved from development by base, so that every variant of a base sits on one side. Cut-offs SHALL be fitted on development and chosen on validation by a rule written before the choice, and SHALL be reported only on a sealed held-out set. A calibration report SHALL give, per split, the label accuracy by confidence band, the share of turns that would act, clarify or abstain, and the number of cases. No held-out case SHALL be read to fit or choose a cut-off. Traces to REQ-0017 (P0, Done), REQ-0020 (P0, Done) and REQ-0022 (P0, Done).

#### Scenario: Splits do not share bases

- **WHEN** the splits are checked
- **THEN** no base appears in more than one of development, validation and held-out

#### Scenario: The choice is reproducible

- **WHEN** the calibration run is replayed from its recordings
- **THEN** it chooses the same cut-offs
