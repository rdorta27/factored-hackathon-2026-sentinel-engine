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

### Requirement: A second sealed set covers openers, subtypes and slots

A new held-out set for `2024Q4-eval-v8` SHALL be written by an author who has not seen prompt v3, its examples or the 018 amendment. Its intent block SHALL hold the v7 categories, openers, status questions, out-of-scope subtypes and slot cases in the four variants, with the expected kind, subtype and slots. Its multi-turn block SHALL name the charge to select, whether to confirm and the expected end (a verified case number, a refusal or a handoff). The set SHALL be reviewed and back-translated as in v7, and SHALL be sealed under a new hash before any v3 call on it. The v7 entry of `measured.json` SHALL stay unchanged. Traces to REQ-0017 (P0, Done), REQ-0020 (P0, Done), REQ-0012 (P0, Done) and REQ-0055 (P0, Done); decision 018.

#### Scenario: Openers and slots are in the set

- **WHEN** the new set is counted
- **THEN** it holds opener, status, out-of-scope subtype and slot cases in each variant

#### Scenario: The author was isolated

- **WHEN** the provenance of the set is read
- **THEN** it states that the author could not read the prompt, the examples or the amendment

#### Scenario: Measured once

- **WHEN** a second measurement of the new hash is attempted
- **THEN** the runner refuses it

### Requirement: A second sealed set covers openers, subtypes, slots and multi-turn resolution

A new held-out set for `2024Q4-eval-v8` SHALL be written by authors who have not seen prompt v3, its examples, its cut-offs or the 018 amendment. Its intent block SHALL hold the v7 categories, openers, status questions, out-of-scope subtypes and slot cases in the four variants, with the expected kind, subtype and slots. Its multi-turn block SHALL name the charge to select, whether to confirm and the expected end (a verified case number, a refusal or a handoff), and SHALL hold only situations whose end the policy sets. Its attack block SHALL cover marked and unmarked prompt injection, unauthorized access, expired session, bad data, tool failure and multilingual ambiguity, and its noisy twins SHALL copy cases of the intent block with small changes. The set SHALL be reviewed and back-translated as in v7, and SHALL be sealed under a new hash before the measurement. A top-up block SHALL add at least 6 bases for each intent with fewer than 10 bases, and SHALL be sealed under its own hash. The v7 entry of `measured.json` SHALL stay unchanged. Traces to REQ-0017 (P0, Done), REQ-0020 (P0, Done), REQ-0012 (P0, Done) and REQ-0055 (P0, Done); decision 018.

#### Scenario: Openers and slots are in the set

- **WHEN** the new set is counted
- **THEN** it holds opener, status, out-of-scope subtype and slot cases in each variant

#### Scenario: Attacks and noisy twins are in the set

- **WHEN** the new set is counted
- **THEN** it holds an attack block and a set of noisy twins, so the gate D7 can be read on it

#### Scenario: The authors were isolated

- **WHEN** the provenance of the set is read
- **THEN** it states that no author could read the prompt, the examples, the cut-offs or the amendment

#### Scenario: Sealing does not use the measurement

- **WHEN** the set is sealed
- **THEN** `measured.json` has no entry for the new hash

#### Scenario: Thin intents get a top-up

- **WHEN** an intent has fewer than 10 bases after the v8 seal
- **THEN** the top-up block adds at least 6 bases for it before the freeze
