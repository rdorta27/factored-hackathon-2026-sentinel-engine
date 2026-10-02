# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
