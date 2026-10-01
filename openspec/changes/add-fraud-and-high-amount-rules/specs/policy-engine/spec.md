## MODIFIED Requirements

### Requirement: Provisional thresholds do not fire
Fraud, high-amount, and staleness entries SHALL exist in every country file. Fraud-score and high-amount thresholds SHALL hold one value per charge currency the country's accounts use (MX: MXN and USD; CO: COP and USD; AR: ARS and USD). The engine SHALL look up the threshold by the charge's own currency. A currency without a value, or a null value, SHALL NOT fire that rule. A score or amount equal to its threshold SHALL NOT fire. Each configured value SHALL record its `source`: either an evidence run (team synthetic policy) or a bank policy reference. Each country file SHALL state whether it is synthetic. Changing a value, its source or the synthetic flag SHALL NOT require a code change. The staleness entry SHALL stay null while decision 27 is open. Traces to REQ-0006 (P0, In progress), REQ-0007 (P0, Done), and REQ-0049 (P2, Done); decisions 25 and 26.

#### Scenario: Null high amount
- **WHEN** `high_amount` has no value for the charge currency and the charge amount is large
- **THEN** amount does not force a handoff

#### Scenario: Amount equal to the threshold
- **WHEN** a test injects a threshold and the charge amount equals it
- **THEN** `amount.high` does not fire

#### Scenario: USD charge on a Mexican account
- **WHEN** an MX account holds a USD charge above the MX USD high-amount value and below the MX MXN value read as a number
- **THEN** `amount.high` fires, because the USD value is the one compared

#### Scenario: Fraud score is compared per currency
- **WHEN** a charge's fraud score is above the threshold of its currency and below the threshold of another currency of the same country
- **THEN** `fraud.score` fires

#### Scenario: Bank values replace synthetic ones
- **WHEN** a country file sets `synthetic: false`, its own per-currency values and a bank policy `source`
- **THEN** the engine applies those values with the same rule ids and no code change

#### Scenario: Currency without a value
- **WHEN** the charge currency has no configured value in the country file
- **THEN** neither `fraud.score` (by score) nor `amount.high` fires for that charge
