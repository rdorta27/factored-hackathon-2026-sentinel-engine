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
configured default model, never to no model. The rule that assigns a turn to a
route SHALL be declared in a decision before it is measured, and SHALL be tuned
on the development split only. Traces to REQ-0019 (P1, In progress) and
decision 016.

#### Scenario: The route is chosen before the call

- **WHEN** a turn is understood
- **THEN** the router picks a route and the model serving that route, and records both

#### Scenario: Unknown route falls back

- **WHEN** a turn does not match a configured route
- **THEN** the router uses the configured default model instead of failing

#### Scenario: Route rule is declared before measuring

- **WHEN** a held-out run uses a route rule
- **THEN** that rule was committed in a decision before the run, and it was tuned only on development cases

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

The router SHALL send only the customer message, the bounded turn window, and an
optional deterministic digest (the last system questions plus the shown
candidate ids, built in code without model reasoning). It SHALL NOT send
`customer_id`, the session token, or any Gold personal-data column, and the
charge fields it reasons over SHALL follow the service contract
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

#### Scenario: Digest carries context without personal data

- **WHEN** the loop supplies the digest with an understanding call
- **THEN** the request carries only system question codes and shown candidate ids, and still no identifier or personal-data column

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
call, and the replayed result and cost SHALL match the live run. A recorded
response SHALL be keyed by model, prompt version, input and repetition index, so
two models or two repetitions of the same input never share a recording. Each
recorded response SHALL carry its `model`, `prompt_version` and repetition, and
SHALL NOT contain personal data, request headers or credentials. Traces to
REQ-0028 (P0, Done) and REQ-0019 (P1, In progress).

#### Scenario: No network call is attempted

- **WHEN** a turn is served from recorded responses
- **THEN** no HTTP connection is opened

#### Scenario: Replay matches the live run

- **WHEN** the same input is served live and then replayed
- **THEN** the understanding result and the recorded cost are the same

#### Scenario: A recorded response carries provenance and no personal data

- **WHEN** a response is recorded
- **THEN** it stores its `model`, `prompt_version` and repetition, and contains no personal data, header or key

#### Scenario: Two models do not share a recording

- **WHEN** the same input is recorded for two models
- **THEN** each model's replay returns its own response

### Requirement: Failure degrades safely

On model error or timeout the router SHALL NOT report success. The loop SHALL
retry a bounded number of times and then reply with a fixed fallback and offer a
handoff, never an unverified answer. Traces to REQ-0021 (P0, Done) and REQ-0026
(P1, Done).

#### Scenario: Model error is not success

- **WHEN** the model call fails or times out after bounded retries
- **THEN** the turn ends in a safe fallback or handoff and no action is reported as done

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

### Requirement: Live responses are recorded once

The system SHALL offer an explicit recording mode that calls the live endpoint
only when no recording exists for the key, and writes the response as a
recording. Outside recording mode no live call SHALL be made by the evaluation.
The API key SHALL be read from the environment only and SHALL never be written
to a recording, log, summary or repository file. Traces to REQ-0028 (P0, Done)
and REQ-0034 (P0, Done).

#### Scenario: Existing recording is not paid twice

- **WHEN** recording mode meets an input that is already recorded for that key
- **THEN** the recording is served and no live call is made

#### Scenario: Key never reaches a file

- **WHEN** a recording session finishes
- **THEN** no written file contains the API key or an authorization header

### Requirement: Cost uses the model's own price

The `cost_usd` of a live call SHALL be computed from the provider's reported
token usage and the input and output price of the model that served it, taken
from a declared price table dated with its source. A model without a declared
price SHALL fail the call in recording mode rather than use a generic price.
Traces to REQ-0055 (P0, In progress) and REQ-0057 (P1, In progress).

#### Scenario: Two models, two prices

- **WHEN** the same tokens are served by a cheap and a strong model
- **THEN** each recorded cost uses that model's price

#### Scenario: Unknown price is refused

- **WHEN** a model has no declared price
- **THEN** recording that model fails with a message naming it

### Requirement: Output is bounded JSON

Each understanding call SHALL request JSON output and SHALL cap the output
tokens, including any reasoning tokens the provider reports. A reply that is
not valid JSON after the cap SHALL count as a JSON failure for model selection
and SHALL degrade safely in the loop. Traces to REQ-0019 (P1, In progress) and
REQ-0026 (P1, Done).

#### Scenario: Capped reply

- **WHEN** a model reply reaches the output cap
- **THEN** the call ends, its tokens are recorded, and an invalid reply is counted as a JSON failure

### Requirement: A prompt version with development examples

The router SHALL support a prompt version that adds a fixed block of examples
before the customer message. Every example SHALL be a development case, and the
example ids SHALL be recorded with the prompt version. The version without
examples SHALL stay available, so both are measured on the same cases. Traces
to REQ-0016 (P0, In progress) and REQ-0017 (P0, In progress).

#### Scenario: Example block is traceable

- **WHEN** the prompt version with examples serves a call
- **THEN** the record names that prompt version, and its example ids are all in the development split
