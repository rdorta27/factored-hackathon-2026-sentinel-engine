# judge-access Specification

## Purpose
Defines the login rule of the public link: no passwordless entry, one shared set of credentials in the submission email, and no password in the repository.

## Requirements

### Requirement: The public link has no passwordless entry

The public deployment SHALL answer 404 on `GET /api/v1/auth/demo` and on `POST /api/v1/auth/demo/{persona}`. The advisor account SHALL need a password that is not in the repository. Traces to REQ-0027 (P0, Done).

#### Scenario: One-click route off

- **WHEN** `SENTINEL_DEMO_AUTH=1` and `SENTINEL_DEMO_PERSONAS=0`
- **THEN** the persona list and the persona login answer 404
- **AND** the advisor login still needs its password

#### Scenario: Default

- **WHEN** `SENTINEL_DEMO_PERSONAS` is unset and `SENTINEL_DEMO_AUTH=1`
- **THEN** the one-click route works as before

### Requirement: Judge credentials stay out of the repository

The users file of the public link SHALL hold only salted password hashes. The plain passwords SHALL exist only in an ignored sheet and in the submission email. The documented fixture passwords SHALL NOT work on the public link. Traces to REQ-0027 (P0, Done) and REQ-0034 (P0, Done).

#### Scenario: Fixture password on the link

- **WHEN** a visitor logs in on the link with a documented fixture password
- **THEN** the login fails

#### Scenario: Judge password on the link

- **WHEN** a judge logs in with an emailed credential
- **THEN** the login works and the session has the expected role and country

### Requirement: The page states that the data is simulated

The entry page SHALL show a notice that the data is simulated whenever Gold is a mock, with or without the one-click entry. Traces to REQ-0032 (P1, Done).

#### Scenario: Mock Gold, no one-click entry

- **WHEN** `gold_source` is `mock` and the one-click route is off
- **THEN** the entry page shows the notice
