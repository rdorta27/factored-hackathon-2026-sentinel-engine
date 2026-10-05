## ADDED Requirements

### Requirement: The repository holds no unused reference app

The repository SHALL NOT keep the `sentinel-login/` folder once nothing serves, imports or tests it. Each reference to the folder in the README, `AGENTS.md`, the docs and the code comments SHALL be removed or rewritten, and decision 009 SHALL record the removal. Archived OpenSpec changes SHALL stay unchanged, because they are history. Traces to REQ-0034 (P0, Done).

#### Scenario: Nothing depends on the folder

- **WHEN** the folder is removed
- **THEN** both test suites pass and the build and the CI workflow do not name the folder

#### Scenario: No dead link

- **WHEN** the links of the Markdown files outside `openspec/changes/archive/` are checked
- **THEN** no relative link points to a missing file

### Requirement: The documentation layout names what each page holds

The repository SHALL NOT keep a `docs/understand/` folder. The overview, the dataset page, the glossary and the official data dictionary SHALL live in folders that name their content. `AGENTS.md`, `README.md`, `docs/README.md` and `team/` SHALL use the new paths. Traces to REQ-0034 (P0, Done) and REQ-0051 (P0, In progress).

#### Scenario: Old path

- **WHEN** a file outside `openspec/changes/archive/` names `docs/understand/`
- **THEN** the link check fails

#### Scenario: Anchors

- **WHEN** a page moves
- **THEN** its headings and anchors stay the same
