# disputes Specification

## Purpose

Turns dispute creation into a deterministic, policy-gated operation whose response proves the work done, so the customer trusts the receipt instead of calling to confirm it.

## Requirements

### Requirement: Policy-gated dispute creation

The system SHALL expose `POST /api/v1/disputes/create` for role `customer`, taking a transaction reference and an idempotency key, and SHALL create a case only when code verifies eligibility: within the configured dispute window, transaction not refunded or reversed, and no prior dispute for it. Traces to REQ-0033 (P0, Pending), REQ-0043 (P1, Pending), and REQ-0048 (P0, Pending).

#### Scenario: Eligible transaction opens a case

- **WHEN** a customer requests a dispute for an eligible transaction with a fresh idempotency key
- **THEN** the system creates exactly one case and returns the Proof-of-Work payload

#### Scenario: Stale transaction is refused with reason

- **WHEN** the transaction is older than the dispute window
- **THEN** the system creates no case and returns the ineligibility reason plus a handoff

#### Scenario: Refunded or already-disputed transaction is refused

- **WHEN** the transaction is refunded, reversed, or already disputed
- **THEN** the system creates no case and returns the reason plus a handoff

#### Scenario: Retried request creates no duplicate

- **WHEN** the same idempotency key arrives twice
- **THEN** the system returns the original result without creating a second case

### Requirement: Proof-of-Work payload

Every created case SHALL return the Proof-of-Work elements: the verified eligibility rule with policy article, the resolution deadline, a downloadable receipt, the human-queue status, and an explicit "no funds held" statement. The payload SHALL carry raw values and translation keys rather than authored prose, and SHALL NOT claim a hold or any movement of money, because the challenge does not authorize it. Traces to REQ-0003 (P0, Pending), REQ-0005 (P0, Pending), and REQ-0004 (P0, Pending).

#### Scenario: Confirmation carries all the elements

- **WHEN** a case is created and verified
- **THEN** the payload contains the rule, the deadline, the receipt reference, the queue status, and the no-funds-held key

#### Scenario: No proof without verification

- **WHEN** the post-creation re-read fails
- **THEN** the system returns a handoff instead of the Proof-of-Work payload

#### Scenario: No hold is claimed anywhere

- **WHEN** any confirmation or receipt is rendered
- **THEN** no text states or implies that funds were frozen, held, or moved

### Requirement: Configurable reference date

The system SHALL use one configurable reference date as its notion of "today" for the dispute window, SHALL display that date to the customer, and SHALL evaluate the window against it rather than the wall clock. The value SHALL come from the `SENTINEL_REFERENCE_DATE` environment variable with the default recorded in the chat capability. Traces to REQ-0039 (P0, Pending) and REQ-0048 (P0, Pending).

#### Scenario: Reference date is visible

- **WHEN** the customer opens the interface or receives a confirmation
- **THEN** the reference date the system used is shown

#### Scenario: Day 89 and day 90 are inside the window

- **WHEN** the transaction is 89 or 90 days before the reference date
- **THEN** the system treats it as eligible

#### Scenario: Day 91 is outside the window

- **WHEN** the transaction is 91 days before the reference date
- **THEN** the system refuses with the window reason

### Requirement: Currency from the account

The system SHALL take every amount and its currency from the account or transaction record, NEVER from the customer's language or country of browsing. Language SHALL affect only how a value is formatted for display. Traces to REQ-0041 (P0, Pending).

#### Scenario: Same amount, different formatting

- **WHEN** the same transaction is displayed in two languages
- **THEN** the currency and value are identical and only the formatting differs

#### Scenario: Country customers keep their currency

- **WHEN** the MX, CO, and AR demo customers each open a dispute
- **THEN** each confirmation shows MXN, COP, and ARS respectively

### Requirement: Business-day resolution deadline

The resolution deadline SHALL be computed in business days from the reference date by one shared calculation, and the same value SHALL be shown on the card and in the receipt. Traces to REQ-0003 (P0, Pending).

#### Scenario: Weekend is not counted

- **WHEN** the reference date plus the SLA in business days crosses a weekend
- **THEN** the deadline lands on the next business day

#### Scenario: One deadline everywhere

- **WHEN** the confirmation and the receipt are compared
- **THEN** they state the same resolution date

### Requirement: Chat delegates creation

`POST /chat` SHALL NOT invent transaction facts; it SHALL resolve the transaction through the Gold seam and create cases only through the disputes service. Traces to REQ-0003 (P0, Pending) and REQ-0006 (P0, Pending).

#### Scenario: Chat confirmation matches the created case

- **WHEN** the chat flow opens a dispute
- **THEN** the confirmation equals the disputes service result field for field
