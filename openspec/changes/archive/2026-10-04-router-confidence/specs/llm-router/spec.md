## ADDED Requirements

### Requirement: The router reports a confidence for its label

When the provider returns token log-probabilities, the router SHALL derive a confidence between 0 and 1 for the label it returns and SHALL record it on the `understand` record next to the label, model, route and prompt version. When log-probabilities are missing for a call, the confidence SHALL be absent and the turn SHALL behave as without cut-offs. The confidence SHALL NOT be shown to the customer. Traces to REQ-0016 (P0, Done), REQ-0025 (P1, Done) and REQ-0002 (P0, Done).

#### Scenario: Confidence is recorded

- **WHEN** a live call returns log-probabilities
- **THEN** the `understand` record carries the label and its confidence

#### Scenario: Missing log-probabilities degrade safely

- **WHEN** a call returns no log-probabilities
- **THEN** the record has no confidence and the turn uses the label as today

### Requirement: Cut-offs map confidence to act, clarify or abstain

When the cut-offs are enabled, a label with confidence at or above `t_act` SHALL be used; between `t_abstain` and `t_act` the turn SHALL ask a clarifying question; below `t_abstain` the turn SHALL ask for clarification and, once the existing clarification limit is reached, offer an advisor. The cut-offs SHALL live in the router configuration with the run they were chosen on, and SHALL NOT override a policy refusal, a handoff rule or the confirm box. Traces to REQ-0002 (P0, Done), REQ-0006 (P0, Done), REQ-0033 (P0, Done) and REQ-0017 (P0, Done).

#### Scenario: A borderline charge asks first

- **WHEN** the label is `charge` with confidence between the cut-offs
- **THEN** the reply is a clarifying question and no charge path runs

#### Scenario: Policy still wins

- **WHEN** a confident label meets a charge the policy refuses
- **THEN** the policy refusal is returned

#### Scenario: Off by default

- **WHEN** the setting is off
- **THEN** the router behaves exactly as v2
