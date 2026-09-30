# llm-router Specification

## Purpose

Routes each understanding call to a model by route, returns the customer's intent
and reply language, reports the model and prompt identity it used, and never
exposes personal data to the model.

## Requirements
### Requirement: Intent and language from the model

The router SHALL classify each customer message into exactly one intent
(`charge`, `missing`, `out_of_scope`, `person`) and detect the reply language
(`es-419` or `pt-BR`), returning both through `ModelPort.understand`. A request
for a person and a request out of scope SHALL be distinguished from a charge
inquiry. Traces to REQ-0001 (P0, In progress) and REQ-0012 (P0, In progress).

#### Scenario: Charge inquiry is understood

- **WHEN** the customer describes an unrecognized charge
- **THEN** the router returns intent `charge` and the detected language

#### Scenario: Portuguese is detected without training data

- **WHEN** the customer writes in Brazilian Portuguese
- **THEN** the router returns language `pt-BR` and the same intent it would for the Spanish equivalent

#### Scenario: Out of scope is not a charge

- **WHEN** the customer asks for a balance, product, card or credit
- **THEN** the router returns intent `out_of_scope` and the loop offers a handoff without opening a dispute

### Requirement: A model per route

The router SHALL select the model by route, so frequent simple turns and
ambiguous or Portuguese turns may be served by different models, without
changing the loop's behavior or outcomes. An unknown route SHALL fall back to a
configured default model, never to no model. Traces to REQ-0019 (P1, Pending)
and decision 010.

#### Scenario: The route is chosen before the call

- **WHEN** a turn is understood
- **THEN** the router picks a route and the model serving that route, and records both

#### Scenario: Unknown route falls back

- **WHEN** a turn does not match a configured route
- **THEN** the router uses the configured default model instead of failing

### Requirement: Model identity is recorded

Every understanding call SHALL report its `model`, `route` and `prompt_version`
through a single describe seam, and the `understand` record SHALL carry those
real values plus `tokens_in`, `tokens_out` and `cost_usd`. No record SHALL keep
the mock placeholders once a real model serves. Traces to REQ-0019 (P1,
Pending) and REQ-0055 (P0, Pending).

#### Scenario: Understand record carries identity and cost

- **WHEN** the prompted router serves an understanding call
- **THEN** the `understand` record carries the model, route, prompt version and numeric token and cost values

#### Scenario: The keyword baseline reports its own identity

- **WHEN** the keyword baseline serves instead
- **THEN** the record still carries non-empty model, route and prompt version, and numeric (zero) token and cost values

### Requirement: No personal data reaches the model

The router SHALL send only the customer message and the bounded turn window. It
SHALL NOT send `customer_id`, the session token, or any Gold personal-data
column, and the charge fields it reasons over SHALL follow the service contract
(numeric amount and fraud score, no name, document or credit score). Traces to
REQ-0047 (P0, In progress).

#### Scenario: No identifier in the request

- **WHEN** an understanding call is sent to a model
- **THEN** the request carries no `customer_id`, no session token and no personal-data column

#### Scenario: Charge fields follow the service contract

- **WHEN** the router extracts or refers to a charge
- **THEN** it uses the contract field names and numeric types, and never a personal-data column

### Requirement: The model never decides permissions or actions

The router SHALL return understanding only. Eligibility, confirmation and every
write SHALL stay in policy and code, so a model output or an injected
instruction SHALL have no effect on permissions or on opening a dispute. Traces
to REQ-0007 (P0, In progress) and REQ-0021 (P0, Done).

#### Scenario: Injected instruction cannot open a dispute

- **WHEN** customer text asks the model to open a dispute or to skip confirmation
- **THEN** no dispute is opened without the structured confirmation and policy

#### Scenario: Model output cannot bypass a rule

- **WHEN** the model returns an intent that policy would reject
- **THEN** the policy outcome is final and the loop does not act on the model's suggestion

### Requirement: Interchangeable model behind one port

The system SHALL run with either the prompted router or the keyword baseline
behind the same port, selected at startup, so the loop and its outcomes do not
depend on which model serves. Traces to REQ-0032 (P1, In progress).

#### Scenario: The baseline runs the same loop

- **WHEN** the application starts with the keyword baseline
- **THEN** every existing loop behavior holds and the suite passes

#### Scenario: The model is selected without editing code

- **WHEN** the application starts with the prompted router
- **THEN** the loop runs unchanged and no code is edited to switch models

### Requirement: Offline replay is deterministic

The system SHALL reproduce a turn from recorded responses without any network
call, and the replayed result and cost SHALL match the live run. Each recorded
response SHALL carry its `prompt_version` and SHALL NOT contain personal data.
Traces to REQ-0028 (P0, Pending) and REQ-0019 (P1, Pending).

#### Scenario: No network call is attempted

- **WHEN** a turn is served from recorded responses
- **THEN** no HTTP connection is opened

#### Scenario: Replay matches the live run

- **WHEN** the same input is served live and then replayed
- **THEN** the understanding result and the recorded cost are the same

#### Scenario: A recorded response carries provenance and no personal data

- **WHEN** a response is recorded
- **THEN** it stores its `prompt_version` and contains no personal data

### Requirement: Failure degrades safely

On model error or timeout the router SHALL NOT report success. The loop SHALL
retry a bounded number of times and then reply with a fixed fallback and offer a
handoff, never an unverified answer. Traces to REQ-0021 (P0, Done) and REQ-0026
(P1, Done).

#### Scenario: Model error is not success

- **WHEN** the model call fails or times out after bounded retries
- **THEN** the turn ends in a safe fallback or handoff and no action is reported as done
