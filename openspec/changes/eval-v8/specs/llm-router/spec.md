## ADDED Requirements

### Requirement: v3 is served by default only after passing the amended rules

The service SHALL serve v3 by default only after `2024Q4-eval-v8` is frozen and v3 meets every rule of the 018 amendment, including the v7 gates and zero unsafe wording. Otherwise `router_v2` SHALL stay the default and the result SHALL be reported as it is. Serving v3 SHALL fail at startup if its examples do not load, and a test SHALL pin the served example ids to the v8 summary. Traces to REQ-0016 (P0, Done) and REQ-0020 (P0, Done); decisions 016 and 018.

#### Scenario: v3 fails a rule

- **WHEN** v3 misses a gate in `eval-v8`
- **THEN** `router_v2` stays the default and the report states the failed rule

#### Scenario: Served examples match the run

- **WHEN** the app starts with v3
- **THEN** its example ids equal those in the `eval-v8` summary, or startup fails
