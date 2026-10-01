# Spec Delta

## MODIFIED Requirements

### Requirement: Role-based landing

After login the interface SHALL route each role to its view: the chat for customers and the read-only ticket view for the advisor. There is no admin view. The chat SHALL render a `handoff` reply as a card with the translated reason and the estimated date. Traces to REQ-0038 (P0, In progress) and REQ-0008 (P0, In progress).

#### Scenario: Login lands on the role view

- **WHEN** a customer or the demo advisor signs in
- **THEN** the browser shows the chat or the ticket view respectively
