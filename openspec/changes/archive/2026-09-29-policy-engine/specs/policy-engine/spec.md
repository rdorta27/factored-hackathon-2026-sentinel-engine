# Spec Delta

## Purpose

Evaluates dispute eligibility in code from a per-country file, and returns one citable rule.

## ADDED Requirements

### Requirement: Evaluate returns one hit
The engine SHALL accept intent, an optional candidate, country, an injected demo date, clarification count, and `person_asks`. It SHALL return one outcome (`explain`, `handoff`, `allow`, or `offer`) and one `rule_id`. It SHALL NOT read the clock, call a model, or store state. The first matching rule SHALL win. Traces to REQ-0007 (P0, In progress), REQ-0033 (P0, Done), and REQ-0048 (P0, Done).

#### Scenario: Two rules match
- **WHEN** a charge is Reversed and the customer has asked for a person twice
- **THEN** the hit is `person.insist` and the status rule is not the cited id

### Requirement: Country is a file, not a branch
Parameters SHALL live in one synthetic file per account country under `config/policy/`. MX, CO, and AR SHALL each have a file. There SHALL be no Brazil account file. An unknown country SHALL NOT inherit MX and SHALL NOT return `allow`. Adding a country SHALL NOT require a new code branch. Traces to REQ-0049 (P2, In progress) and REQ-0031.

#### Scenario: Unknown country
- **WHEN** the request country has no file
- **THEN** the outcome is not `allow`

#### Scenario: Portuguese reply, Mexican account
- **WHEN** the reply language is `pt-BR` and the account country is MX
- **THEN** the engine loads the MX file and does not look for a Brazil file

### Requirement: Provisional thresholds do not fire
Fraud, high-amount, and staleness entries SHALL exist and SHALL be marked provisional while decisions 25, 26, and 27 are open. A null value SHALL NOT fire that rule. An amount equal to a configured threshold SHALL NOT fire `amount.high`. A charge whose currency is not the file currency SHALL NOT fire `amount.high`. Traces to REQ-0007 (P0, In progress) and REQ-0049 (P2, In progress).

#### Scenario: Null high amount
- **WHEN** `high_amount` is null and the charge amount is large
- **THEN** amount does not force a handoff

#### Scenario: Amount equal to the threshold
- **WHEN** a test injects a threshold and the charge amount equals it
- **THEN** `amount.high` does not fire

### Requirement: Window uses the demo date
Age SHALL be demo date minus transaction date, in days. The engine SHALL NOT call the wall clock. Day 90 SHALL NOT cite `window.expired`. Day 91 SHALL. The Gold eligibility flag SHALL NOT override that result. Traces to REQ-0043 (P1, In progress) and decision 003.

#### Scenario: Static data does not use today
- **WHEN** the wall clock is after the dataset end and the injected demo date makes the charge 90 days old
- **THEN** the window rule does not block the dispute

### Requirement: Open is rejected unless the hit is allow
Before `open_dispute`, including the confirmation turn, the loop SHALL evaluate again. A hit other than `allow` SHALL reject the write and cite `rule_id`. The category port SHALL NOT be called unless the hit is `allow`. Traces to REQ-0006 (P0, In progress), REQ-0033 (P0, Done), and REQ-0048 (P0, Done).

#### Scenario: Confirmation turn re-checks
- **WHEN** a confirm box was shown and the confirmation turn now hits `window.expired`
- **THEN** `open_dispute` is not called

#### Scenario: Proposed open on a reversed charge
- **WHEN** the model proposes `open_dispute` and the hit is `status.reversed`
- **THEN** the write is rejected and the category port is not called
