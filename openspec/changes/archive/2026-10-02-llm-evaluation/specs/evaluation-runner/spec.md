# Spec Delta

## MODIFIED Requirements

### Requirement: Versioned labelled case set

The harness SHALL read a versioned case set in JSON lines where each case
carries an id, locale (`es-419` or `pt-BR`), country (`MX`, `CO` or `AR`), the
customer turns, component labels (`expected_intent`, and `expected_category`
where a dispute applies), system labels (`expected_outcome`, `requires_handoff`),
a tag set (`edge`, `adversarial`, `noisy`) and a split (`development` or
`held_out`). Cases derived from a base situation SHALL also carry `base_id` and
`variant` (`es-MX`, `es-CO`, `es-AR` or `pt-BR`), and a noisy case SHALL name its
`perturbation`. The variant SHALL agree with the locale and country. The text
SHALL be team-written and declared as simulation, never a dataset row. Traces
to REQ-0017 (P0, In progress) and REQ-0031 (P0, Done).

#### Scenario: Every case is fully labelled

- **WHEN** the case set is loaded
- **THEN** each case has an id, a locale, a country, its turns and both label groups

#### Scenario: No dataset row is used as a case

- **WHEN** a case is authored
- **THEN** its text is team-written and no dataset row is copied into the set

#### Scenario: Variant contradicts locale

- **WHEN** a case has variant `es-AR` and locale `pt-BR`, or variant `es-AR` and country `MX`
- **THEN** loading fails and names the case

### Requirement: Baseline and system on the same held-out set

The harness SHALL run the keyword baseline, the router without examples and the
router with examples over the same cases on the same split, so a result compares
like with like. A sealed held-out set SHALL be measured once: the harness SHALL
keep a committed record of measured seal hashes and SHALL refuse a second
held-out measurement of the same hash. Traces to REQ-0020 (P0, In progress) and
REQ-0017 (P0, In progress).

#### Scenario: Both models see the same cases

- **WHEN** the comparison is produced
- **THEN** the baseline and both router versions were run on the identical case set, and the summary records it

#### Scenario: A case never appears in both splits

- **WHEN** the splits are applied
- **THEN** no case id appears in both the development and the held-out split

#### Scenario: Second measurement is refused

- **WHEN** a held-out measurement is started on a seal hash already in the measured record
- **THEN** the harness stops before any model call and names the earlier run

### Requirement: Every result carries n, mix, versions and variability

Each reported metric SHALL carry its sample size, the case mix, the model and
prompt versions and the variability across runs, and the report SHALL list the
failures, not only the successes. Metrics SHALL be reported per variant (es-MX,
es-CO, es-AR, pt-BR) and per intent as well as overall, each with its n and a
95% interval. A breakdown whose interval is wider than ±10 points SHALL be
labelled descriptive. Traces to REQ-0022 (P0, In progress), REQ-0019 (P1, In
progress), REQ-0024 (P1, In progress) and REQ-0013 (P0, In progress).

#### Scenario: A metric without n is not reported

- **WHEN** a metric is written
- **THEN** it carries its sample size and the case mix

#### Scenario: Failures appear in the report

- **WHEN** a case fails
- **THEN** the report lists it with its count and reason

#### Scenario: Thin breakdown is labelled

- **WHEN** a per-variant or per-intent interval is wider than ±10 points
- **THEN** the report labels that breakdown descriptive

## ADDED Requirements

### Requirement: Paired comparison with intervals

The harness SHALL compare two versions case by case on the same cases, and
report the cases each version fixes and breaks, the net difference and its 95%
interval. Intervals SHALL be computed by resampling base situations, not single
cases, because the four variants of a base are not independent. For variants it
SHALL report, per variant, the net loss in shared bases against the best
variant, with the list of the bases lost. Traces to REQ-0016 (P0, In progress)
and REQ-0012 (P0, In progress).

#### Scenario: Fixed and broken cases are named

- **WHEN** the router is compared with the baseline
- **THEN** the summary lists the ids the router fixes and the ids it breaks, and the net difference with its interval

#### Scenario: Variant loss is counted in shared bases

- **WHEN** es-AR is wrong and es-MX is right on the same base
- **THEN** that base counts as an es-AR loss and appears in its list

### Requirement: Stability comes from recorded repetitions

Stability SHALL be computed from separate recorded repetitions of the same
input, never from replaying one recording several times. The report SHALL state
on how many cases repetitions were recorded. Traces to REQ-0016 (P0, In
progress) and REQ-0022 (P0, In progress).

#### Scenario: Replayed repetitions are not stability

- **WHEN** only one recording exists for a case
- **THEN** that case is left out of the stability metric and the n says so

### Requirement: Spend cap

A run that makes live calls SHALL accept a spend cap in USD, SHALL stop before a
call that would exceed it based on the cost so far, and SHALL record the spend
and whether the cap stopped the run. A run stopped by the cap SHALL NOT be
frozen as a measurement. Traces to REQ-0055 (P0, In progress) and REQ-0057 (P1,
In progress).

#### Scenario: Cap reached

- **WHEN** the cost so far plus the next call's estimate exceeds the cap
- **THEN** the run stops, records the spend, and does not freeze a summary

### Requirement: Selection runs on development only

Model selection and route tuning SHALL run on the development split only and
SHALL write their own evidence run, separate from the held-out measurement. A
selection run that reads a held-out case SHALL fail. Traces to REQ-0017 (P0, In
progress) and REQ-0019 (P1, In progress).

#### Scenario: Held-out case in a selection run

- **WHEN** a selection run is given a held-out case
- **THEN** it fails before any model call
