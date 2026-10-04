## ADDED Requirements

### Requirement: Contract v3 reads more without deciding

The router SHALL return, in one call: `kind` (`charge`, `status`, `missing`, `out_of_scope`, `person`), an optional `subtype`, `language`, `not_mine`, optional `slots` (merchant words, a numeric amount, a date phrase, a "twice" flag), an optional `reply_draft` and `confidence`. Every new field SHALL be optional, so v1, v2 and the keyword baseline still fit. The keyword baseline SHALL NOT change. No field SHALL decide a permission, an eligibility, a confirmation or a handoff. Traces to REQ-0002 (P0, Done), REQ-0016 (P0, Done) and REQ-0033 (P0, Done).

#### Scenario: Loan request

- **WHEN** prompt v3 reads "quiero un préstamo"
- **THEN** the result is `out_of_scope` with subtype `loan`

#### Scenario: Amount in words

- **WHEN** prompt v3 reads "un cobro de mil pesos"
- **THEN** the amount slot is 1000

#### Scenario: Status of a charge

- **WHEN** prompt v3 reads "quiero ver el estado de mi último cargo"
- **THEN** the result is `status`

#### Scenario: The baseline is unchanged

- **WHEN** the baseline reads any case of `2024Q4-eval-v7`
- **THEN** its label is the same as in that run

### Requirement: Drafts carry placeholders and pass a validator

A `reply_draft` SHALL contain no value: merchants, amounts, dates and statuses SHALL appear only as placeholders that code fills from verified facts. A validator SHALL reject a draft with a digit outside a placeholder, an unknown placeholder, a name or date not in the verified facts, a promise, a wrong language or a length over the limit, and SHALL record the reason. A rejected draft SHALL fall back to the template. Turns that decide SHALL never use a draft. Traces to REQ-0003 (P0, Done), REQ-0005 (P0, Done) and REQ-0021 (P0, Done); decision 024.

#### Scenario: Draft with an invented amount

- **WHEN** a draft says "te devolveremos 500 pesos"
- **THEN** the validator rejects it and the reply uses the template

#### Scenario: Draft on a decision turn

- **WHEN** the turn shows a confirm box
- **THEN** the reply uses the template and ignores the draft

### Requirement: Prompt v3 uses development examples only

Prompt v3 SHALL define each intent, subtype and slot in one line, and SHALL use only development examples, whose ids are recorded with the version. Versions v1 and v2 SHALL stay available. Traces to REQ-0016 (P0, Done) and REQ-0017 (P0, Done).

#### Scenario: Examples are development cases

- **WHEN** v3 serves a call
- **THEN** the record names v3 and every example id is in the development split

### Requirement: v3 is served only after passing the amended rules

The service SHALL serve v3 by default only after `2024Q4-eval-v8` is frozen and v3 meets every rule of the 018 amendment, including the v7 gates and zero unsafe wording. Otherwise v2 SHALL stay the default. Serving v3 SHALL fail at startup if its examples do not load, and a test SHALL pin the served example ids to the v8 summary. Traces to REQ-0016 (P0, Done) and REQ-0020 (P0, Done); decisions 016 and 018.

#### Scenario: v3 fails a rule

- **WHEN** v3 misses a gate in `eval-v8`
- **THEN** v2 stays the default and the report states the failed rule
