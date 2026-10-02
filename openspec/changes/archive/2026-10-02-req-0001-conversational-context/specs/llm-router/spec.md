# Spec Delta

## MODIFIED Requirements

### Requirement: No personal data reaches the model
The router SHALL send only the customer message, the bounded turn window, and an optional deterministic digest (the last system questions plus the shown candidate ids, built in code without model reasoning). It SHALL NOT send `customer_id`, the session token, or any Gold personal-data column, and the charge fields it reasons over SHALL follow the service contract (numeric amount, no name, document or credit score). It SHALL NOT send the fraud score: the policy engine reads it from Gold, the model never needs it, and data the model does not need does not leave for an external provider. Traces to REQ-0047 (P0, In progress) and REQ-0033 (P0, Done).

#### Scenario: No identifier in the request
- **WHEN** an understanding call is sent to a model
- **THEN** the request carries no `customer_id`, no session token and no personal-data column

#### Scenario: Charge fields follow the service contract
- **WHEN** the router extracts or refers to a charge
- **THEN** it uses the contract field names and numeric types, and never a personal-data column

#### Scenario: Fraud score stays out of the request
- **WHEN** a charge with a fraud score is passed to the router
- **THEN** the request is rejected before it is sent, and the prompt never asks for a fraud score

#### Scenario: Digest carries context without personal data
- **WHEN** the loop supplies the digest with an understanding call
- **THEN** the request carries only system question codes and shown candidate ids, and still no identifier or personal-data column
