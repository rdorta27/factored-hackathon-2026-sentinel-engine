## MODIFIED Requirements

### Requirement: No personal data reaches the model

The router SHALL send only the customer message and the bounded turn window. It
SHALL NOT send `customer_id`, the session token, or any Gold personal-data
column, and the charge fields it reasons over SHALL follow the service contract
(numeric amount, no name, document or credit score). It SHALL NOT send the
fraud score: the policy engine reads it from Gold, the model never needs it, and
data the model does not need does not leave for an external provider. Traces to
REQ-0047 (P0, In progress) and REQ-0033 (P0, Done).

#### Scenario: No identifier in the request

- **WHEN** an understanding call is sent to a model
- **THEN** the request carries no `customer_id`, no session token and no personal-data column

#### Scenario: Charge fields follow the service contract

- **WHEN** the router extracts or refers to a charge
- **THEN** it uses the contract field names and numeric types, and never a personal-data column

#### Scenario: Fraud score stays out of the request

- **WHEN** a charge with a fraud score is passed to the router
- **THEN** the request is rejected before it is sent, and the prompt never asks for a fraud score

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
