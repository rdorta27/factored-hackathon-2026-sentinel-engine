# Spec Delta

## Purpose

Restricts every endpoint to the role stored in the server-side session and gives advisors and admins exactly the data their job needs, nothing more.

## ADDED Requirements

### Requirement: Session roles enforced in code

The system SHALL store one role per session (`customer`, `advisor`, `admin`) and SHALL check it on every role-restricted endpoint. A role failure SHALL return 403 and record `access_denied`. Traces to REQ-0007 (P0, Pending) and REQ-0027 (P0, Pending).

#### Scenario: Customer cannot reach advisor endpoints

- **WHEN** a customer session calls an advisor endpoint
- **THEN** the system returns 403 and records `access_denied`

#### Scenario: Advisor cannot reach admin endpoints

- **WHEN** an advisor session calls an admin endpoint
- **THEN** the system returns 403 and records `access_denied`

#### Scenario: No role means no access

- **WHEN** a request has a valid session without a usable role
- **THEN** the system returns 403 for any role-restricted endpoint

### Requirement: Advisor queue with minimum privilege

The advisor SHALL see only escalated cases with the structured summary (request, verified facts, actions taken, evidence, open questions) and SHALL be able to claim a case and change its state. The advisor SHALL NOT see the full customer profile or other customers' cases. Traces to REQ-0008 (P0, Pending), REQ-0011 (P0, Pending), and REQ-0046 (P2, Pending).

#### Scenario: Handoff appears in the queue

- **WHEN** a chat escalates to `handoff`
- **THEN** the case appears in the advisor queue with the structured summary and no raw transcript

#### Scenario: Advisor claims and advances a case

- **WHEN** an advisor claims an open case and sets a new state
- **THEN** the queue reflects the new owner and state, and the change is audited

### Requirement: Read-only admin observability

The admin SHALL see the audit log and basic counts (logins, failures, lockouts, handoffs, denied access) and SHALL NOT see full conversation contents. Traces to REQ-0025 (P1, Pending) and REQ-0029 (P1, Pending).

#### Scenario: Admin counts match the audit log

- **WHEN** an admin requests metrics
- **THEN** every count equals the corresponding audit events, and no message text is included

### Requirement: Documented mock users per role

The repository SHALL document one demo credential per role, labeled as false test-only values. Traces to REQ-0028 (P0, Pending).

#### Scenario: Each role can sign in from docs alone

- **WHEN** a reviewer follows the documented credential for a role
- **THEN** the session carries that role and lands on the matching view
