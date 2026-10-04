## ADDED Requirements

### Requirement: The chat capacity is measured

A load run SHALL drive `POST /api/v1/chat` on one process with recorded model answers, at increasing request rates, under the CPU and memory limits of the deployed replica. It SHALL report requests per second, p50 and p95 latency, the error rate and the 429 count for each rate. The run SHALL be frozen write-once. Traces to REQ-0053 (P0, Done).

#### Scenario: Rate above the limit

- **WHEN** the request rate is above what one replica serves
- **THEN** the run reports the rate where p95 or the error rate passes its limit
