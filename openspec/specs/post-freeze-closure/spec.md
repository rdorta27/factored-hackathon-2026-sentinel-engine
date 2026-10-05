# post-freeze-closure Specification

## Purpose
Defines the closing steps after the code freeze: the freeze record, the final measurement and the public redeploy.

## Requirements

### Requirement: The freeze is recorded before any measurement

The owner SHALL confirm the freeze after all code plans are merged, the served configuration is chosen and `scripts/e2e_check.py` passes against the local service. The freeze commit and the `bundle_hash` of `/health` SHALL be recorded. Traces to REQ-0016 (P0, Done) and REQ-0035 (P0, Done); decision 018.

#### Scenario: Gate without confirmation

- **WHEN** the owner has not confirmed the freeze
- **THEN** no measurement or frozen run starts

### Requirement: The sealed v8 set is measured once

`2024Q4-eval-v8` SHALL be measured once on each sealed hash (the v8 set and its top-up block), with three repeats of the high-risk subset, and the measured commit SHALL be recorded. The runner SHALL refuse a second measurement of the same hash. Traces to REQ-0016 (P0, Done) and REQ-0020 (P0, Done); decision 018.

#### Scenario: Measured once

- **WHEN** a second measurement of a v8 hash is attempted
- **THEN** the runner refuses it

### Requirement: v3 is served by default only after passing the amended rules

The service SHALL serve v3 by default only after `2024Q4-eval-v8` is frozen and v3 meets every rule of the 018 amendment, including the v7 gates and zero unsafe wording. Otherwise `router_v2` SHALL stay the default and the result SHALL be reported as it is. Serving v3 SHALL fail at startup if its examples do not load, and a test SHALL pin the served example ids to the v8 summary. Traces to REQ-0016 (P0, Done) and REQ-0020 (P0, Done); decisions 016 and 018.

#### Scenario: v3 fails a rule

- **WHEN** v3 misses a gate in `eval-v8`
- **THEN** `router_v2` stays the default and the report states the failed rule

#### Scenario: Served examples match the run

- **WHEN** the app starts with v3
- **THEN** its example ids equal those in the `eval-v8` summary, or startup fails

### Requirement: Router errors are analyzed with concrete cases

After the measurement, a page SHALL list the most frequent confusions with case ids, the likely cause and the kind of fix (prompt, policy or data). It SHALL show the number of bases for each intent and mark each intent with fewer than 10 bases as descriptive. It SHALL cite `summary.json` fields and SHALL label the cases as team-written simulation. Traces to REQ-0016 (P0, Done) and REQ-0017 (P0, Done).

#### Scenario: Intent with few bases

- **WHEN** an intent has fewer than 10 bases in the sealed set
- **THEN** the page marks its interval as descriptive and makes no claim from it

### Requirement: Tool failures are measured as a rate

A fault-injection run SHALL inject model timeouts, model errors, invalid model JSON, slow Gold, Gold errors and case-store errors. For each fault it SHALL report the outcome, the added latency, and the share of turns that end in a safe reply or a handoff, with counts and denominators. Traces to REQ-0021 (P0, Done) and REQ-0026 (P1, Done).

#### Scenario: Model timeout

- **WHEN** the model times out on every call
- **THEN** the keyword baseline answers each turn and the run counts no unsafe outcome

### Requirement: The chat capacity is measured

A load run SHALL drive `POST /api/v1/chat` on one process with recorded model answers, at increasing request rates, under the CPU and memory limits of the deployed replica. It SHALL report requests per second, p50 and p95 latency, the error rate and the 429 count for each rate. The run SHALL be frozen write-once. Traces to REQ-0053 (P0, Done).

#### Scenario: Rate above the limit

- **WHEN** the request rate is above what one replica serves
- **THEN** the run reports the rate where p95 or the error rate passes its limit

### Requirement: The final redeploy is proved and queried

After the final redeploy, a check SHALL confirm the served model and prompt version, the `bundle_hash` recorded at the gate, the locale keys of the merged code, the demo personas and the three demo cases. Saved queries SHALL report turns, p50 and p95 latency, failed or timed-out steps, handoffs and cost per account country, outcome and language. Results SHALL be recorded as aggregates without identifiers. Traces to REQ-0035 (P0, Done), REQ-0050 (P1, Done) and REQ-0052 (P0, In progress).

#### Scenario: The served code is the measured code

- **WHEN** `/health` is fetched after the redeploy
- **THEN** its `bundle_hash` equals the hash recorded at the gate

#### Scenario: Queries return per-country aggregates

- **WHEN** the queries run after demo traffic
- **THEN** they return one row per country, outcome and language with counts and latency percentiles, and no trace id or text
