# sealed-case-set Specification

## Purpose

Defines how the evaluation cases are written, sized, reviewed and sealed, so the router-versus-baseline result rests on cases nobody tuned against and on enough cases per language variant to support each decision.

## Requirements

### Requirement: Base situations rendered in four variants

Each held-out and development case SHALL derive from a base situation with a stable `base_id`. A base situation fixes the intent, amount, merchant and expected outcome. It SHALL be rendered in four variants: es-MX, es-CO, es-AR and pt-BR. The Spanish variants SHALL use the vocabulary of their country glossary, and the pt-BR variant SHALL be a customer of a MX, CO or AR account writing in Portuguese (decision 017). Traces to REQ-0012 (P0, Done), REQ-0024 (P1, Done) and REQ-0044 (P1, Pending).

#### Scenario: One base, four renderings

- **WHEN** a base situation is added to the set
- **THEN** four cases with the same `base_id`, intent, amount, merchant and expected outcome exist, one per variant

#### Scenario: Regional vocabulary is used

- **WHEN** the es-AR variant of a base is written
- **THEN** it uses es-AR forms from the es-AR glossary (for example voseo), not a copy of the es-MX text

### Requirement: Set sizes support each decision

The held-out set SHALL hold at least 70 base situations (280 cases), with at least 25 cases per intent and ambiguous wording included on purpose. The development set SHALL hold at least 30 base situations (120 cases). The noisy block SHALL hold at least 50 twins of held-out cases carrying one declared perturbation each (date ±3 days, amount ±15%, truncated name, self-correction). The attack block SHALL hold at least 75 cases, including prompt injection in pt-BR. Each size and the margin it supports SHALL be stated in the report. Traces to REQ-0016 (P0, Done), REQ-0022 (P0, Done) and REQ-0021 (P0, Done).

#### Scenario: Undersized set is refused

- **WHEN** a held-out set has fewer than 70 bases or an intent below 25 cases
- **THEN** sealing is refused and the shortfall is named

#### Scenario: A noisy twin names its perturbation

- **WHEN** a noisy case is added
- **THEN** it references its held-out `base_id` and variant and names exactly one perturbation

### Requirement: Variants are reviewed through Spanish

Every variant not written directly by the team SHALL be back-translated to Spanish by a different model than the one that wrote it. A team member SHALL check the back-translation against the base for meaning, amount, merchant and intent. A variant that drifts SHALL be fixed or dropped, never kept as is. The review outcome SHALL be recorded per case. Traces to REQ-0013 (P0, In progress) and decision 017.

#### Scenario: Drifting variant is dropped

- **WHEN** a back-translation changes the amount or the intent
- **THEN** the variant is fixed or removed before sealing, and the review record says which

### Requirement: Held-out set is sealed before measuring

The held-out set SHALL be sealed by recording a content hash and the authoring date in a committed seal record before any model or baseline is measured on it. After sealing, no held-out case SHALL be edited, added or removed. Held-out cases SHALL NOT be used as prompt examples, for model selection or for route tuning. The held-out cases SHALL NOT be written by the person who tunes the prompt. Traces to REQ-0017 (P0, Done) and REQ-0020 (P0, Done).

#### Scenario: Edited sealed set is detected

- **WHEN** a held-out file changes after sealing
- **THEN** its hash no longer matches the seal record and the runner refuses to measure it

#### Scenario: Examples come only from development

- **WHEN** the prompt with examples is built
- **THEN** every example id belongs to the development split

### Requirement: Earlier held-out cases are retired

The 10 held-out cases measured in runs `2024Q4-eval-v1` to `v6` SHALL move to the development split and SHALL NOT appear in the new sealed set. Traces to REQ-0017 (P0, Done).

#### Scenario: A measured case is not sealed again

- **WHEN** the new held-out set is sealed
- **THEN** none of its texts or ids matches a case measured in an earlier run
