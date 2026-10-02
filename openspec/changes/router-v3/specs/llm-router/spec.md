## ADDED Requirements

### Requirement: Prompt v3 defines every intent and covers openers

The router SHALL offer a prompt version `v3` that defines each of the four intents in one line, classifies greetings, introductions, thanks and "I have a problem" without details as `missing`, and adds to the v2 example block only development cases. Its example ids SHALL be recorded with the version and SHALL all be in the development split. Versions `v1` and `v2` SHALL stay available. The label set SHALL stay `charge`, `missing`, `out_of_scope` and `person`. Traces to REQ-0016 (P0, Done), REQ-0017 (P0, In progress) and REQ-0012 (P0, Done).

#### Scenario: A greeting is missing, not out of scope

- **WHEN** v3 classifies "hola, me llamo Karl"
- **THEN** the label is `missing`

#### Scenario: Greeting with a request keeps the request

- **WHEN** v3 classifies "hola, no reconozco un cargo de 320 en Cafe Central"
- **THEN** the label is `charge`

#### Scenario: Examples are development cases

- **WHEN** v3 serves a call
- **THEN** the record names v3 and every example id is in the development split

### Requirement: v3 is served only after passing the amended rules

The service SHALL serve v3 only after `2024Q4-eval-v8` is frozen and v3 meets every rule of the 018 amendment, including the v7 gates. Otherwise v2 SHALL stay served and the result SHALL be reported as it is. Serving v3 SHALL load its examples through the evaluation loader and SHALL fail at startup if they do not load, and a test SHALL pin the served example ids to those recorded in the v8 summary. Traces to REQ-0016 (P0, Done) and REQ-0020 (P0, Done); decisions 016 and 018.

#### Scenario: v3 fails a rule

- **WHEN** v3 misses a gate in `eval-v8`
- **THEN** v2 stays served and the report states the failed rule

#### Scenario: Served examples match the run

- **WHEN** the app starts with v3
- **THEN** its example ids equal those in the `eval-v8` summary, or startup fails
