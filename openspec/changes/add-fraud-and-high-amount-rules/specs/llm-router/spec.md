## ADDED Requirements

### Requirement: Not-mine claim is reported, not decided

The understanding step SHALL report whether the customer explicitly states the charge was not made by them (for example "no fui yo", "alguien usó mi tarjeta", "não fui eu", "clonaram meu cartão"). Saying a charge is not recognized ("no reconozco este cargo", "não reconheço esta cobrança") SHALL NOT count as that claim. The keyword baseline and the prompted router SHALL report it in the same field, in es-419 and pt-BR. The claim SHALL only feed the policy engine; the model SHALL NOT decide the handoff. Traces to REQ-0006 (P0, In progress), REQ-0012 (P0, In progress) and REQ-0033 (P0, Done); decision 25.

#### Scenario: Spanish not-mine claim

- **WHEN** the customer writes "no fui yo, alguien usó mi tarjeta"
- **THEN** the understanding output reports the claim and the engine hands off citing `fraud.claim`

#### Scenario: Portuguese not-mine claim

- **WHEN** the customer writes "não fui eu"
- **THEN** the understanding output reports the claim

#### Scenario: Unrecognized is not a claim

- **WHEN** the customer writes "no reconozco este cargo"
- **THEN** the claim is not reported and the dispute path continues
