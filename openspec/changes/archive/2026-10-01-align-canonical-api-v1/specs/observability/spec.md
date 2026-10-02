# Spec Delta

## MODIFIED Requirements

### Requirement: One closing record per turn

Every `POST /api/v1/chat` turn SHALL emit exactly one closing record with the final outcome and aggregated cost and latency, sharing the turn `trace_id`, including turns that end in error or handoff so failures stay measurable. When the turn ends in `handoff`, the closing record SHALL carry the same advisor package the reply carries, checked for personal data like every other field. Traces to REQ-0055 (P0, In progress), REQ-0025 (P1, In progress), and REQ-0008 (P0, In progress).

#### Scenario: Failed turns stay measurable

- **WHEN** a turn ends in an error or an unknown-charge handoff
- **THEN** a closing record with that outcome and numeric aggregates still exists under the turn `trace_id`

#### Scenario: Handoff package is in the log

- **WHEN** a turn ends in `handoff`
- **THEN** its closing record carries the package equal to the reply's package
