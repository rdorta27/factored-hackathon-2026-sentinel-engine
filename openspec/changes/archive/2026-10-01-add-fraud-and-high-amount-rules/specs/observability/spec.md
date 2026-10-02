## ADDED Requirements

### Requirement: Decisions record the policy version

Every `decide` record SHALL carry, next to `policy_rule`, the version of the country policy file that produced the decision (a content hash or version id) and whether that file is synthetic. Traces to REQ-0029 (P1, Done), REQ-0025 (P1, Done) and REQ-0006 (P0, In progress); decisions 25 and 26.

#### Scenario: A past case shows the values in force

- **WHEN** a policy file value changes after a case was decided
- **THEN** the earlier `decide` record still names the previous file version, so the case can be traced to the values then in force

#### Scenario: Synthetic flag is visible

- **WHEN** the engine decides with the team's synthetic policy
- **THEN** the `decide` record marks the policy as synthetic
