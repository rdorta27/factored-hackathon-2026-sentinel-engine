## MODIFIED Requirements

### Requirement: Reference thresholds

The run SHALL persist transaction-amount and fraud-score percentiles grouped by the customer's account country (from `customers.country`) and the charge currency, never by `transaction_country` alone and never pooling amounts of different currencies. Country names SHALL be normalized to `México`, `Colombia` and `Argentina` before grouping. The run SHALL also persist the share of products per account country and currency and the count of transactions with an empty `amount_usd`, with their denominators. Traces to REQ-0006 (P0, In progress), REQ-0016 (P0, In progress) and REQ-0015 (P0, In progress); decisions 25 and 26.

#### Scenario: Thresholds are grounded in data

- **WHEN** the thresholds section is written
- **THEN** it reports the amount and fraud-score percentiles per account country and charge currency, each with its count

#### Scenario: Currencies are never pooled

- **WHEN** an account country has charges in its local currency and in USD
- **THEN** the run reports two separate groups and no percentile mixes both

#### Scenario: Country spelling variants collapse

- **WHEN** the source carries both `Mexico` and `México`
- **THEN** both are counted under `México` and the run reports how many rows were normalized
