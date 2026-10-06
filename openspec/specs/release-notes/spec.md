# release-notes Specification

## Purpose
Defines the release record: a changelog, a contributor guide and the release notes that the owner writes before each tag.

## Requirements

### Requirement: The repository records its progress

The repository SHALL hold a `CHANGELOG.md` with one entry per merged pull request and a `CONTRIBUTING.md` that explains the branch, pull request, commit, plan and evidence rules. The release notes of each tag SHALL be written in the repository before the tag is created. Traces to REQ-0034 (P0, Done) and REQ-0051 (P0, In progress).

#### Scenario: A pull request merges

- **WHEN** a pull request merges
- **THEN** the changelog has one entry for it

#### Scenario: A tag is planned

- **WHEN** the owner is about to create a tag
- **THEN** the release notes and the exact commands are already in `docs/build/delivery.md`

### Requirement: The submission has a checklist with proofs

`docs/build/delivery.md` SHALL hold a table of the submission items (repository, deployed link, slides, video, email, Pages, secret scan, tests). Each row SHALL have an owner and a proof. Traces to REQ-0035 (P0, Done), REQ-0036 (P0, Done) and REQ-0037 (P0, Done).

#### Scenario: An item has no proof

- **WHEN** a row has no proof
- **THEN** the checklist does not mark it as done

### Requirement: The freeze procedure exists before the gate

`docs/build/delivery.md` SHALL hold the freeze procedure before gate G3: what must be merged, the order of the last checks (`scripts/e2e_check.py`, `scripts/e2e_check.py --access-check`, the test suites and the secret scan) and the rule that nobody changes code after the last check. Traces to REQ-0035 (P0, Done) and REQ-0052 (P0, In progress).

#### Scenario: Gate G3

- **WHEN** the owner confirms the freeze
- **THEN** the procedure is already in `docs/build/delivery.md`
