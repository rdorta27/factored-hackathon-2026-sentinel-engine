## ADDED Requirements

### Requirement: The project site is static and in English

The repository SHALL contain a static site in `site/`, in English, that describes the product, how it works, the measured results, the demo cases and the links to the live demo and the repository. A workflow SHALL publish `site/` to GitHub Pages from `main`. Traces to REQ-0051 (P0, In progress) and REQ-0056 (P0, In progress).

#### Scenario: Publication

- **WHEN** a change to `site/` merges into `main`
- **THEN** the workflow publishes the site to GitHub Pages

### Requirement: Site numbers come from the evidence

Each number on the site SHALL come from a field of a frozen `summary.json` through `site/numbers.json`, and SHALL show its type: simulation, test suite or projection. A test SHALL fail if a number differs from the evidence. Traces to REQ-0022 (P0, Done) and REQ-0031 (P0, Done).

#### Scenario: A stale number

- **WHEN** a frozen run changes and `site/numbers.json` is not regenerated
- **THEN** the test fails and names the number
