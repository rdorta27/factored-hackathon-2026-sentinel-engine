# Spec Delta

## ADDED Requirements

### Requirement: Handoff filed as a ticket

Every `handoff` reply SHALL be filed as a case with `kind=handoff`, `status=Escalated`, the reply's reference and reason key, and the full advisor package, so the human side receives the ticket and why it was raised. Traces to REQ-0008 (P0, In progress) and REQ-0011 (P0, In progress).

#### Scenario: Insistent customer leaves a ticket

- **WHEN** the customer asks for a person a second time
- **THEN** the case list shows an escalated handoff with the reply's reference, and the stored package equals the reply's package
