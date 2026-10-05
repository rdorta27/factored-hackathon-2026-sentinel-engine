# evidence-index Specification

## Purpose
Defines the evidence index: each frozen run with its status, its data type and the requirements that it supports.

## Requirements

### Requirement: Every frozen run is listed in the evidence index

`evidence/README.md` SHALL list each frozen run with its status (current or superseded), its data type (dataset, simulation, mock store, replay, test suite or projection) and the requirements that it supports. A run that is not in the index SHALL not be cited by another document. Traces to REQ-0031 (P0, Done) and REQ-0013 (P0, In progress).

#### Scenario: A new run lands

- **WHEN** a new run folder is committed under `evidence/`
- **THEN** `evidence/README.md` lists it with its status and data type in the same pull request

#### Scenario: A document cites a run

- **WHEN** a document cites a run
- **THEN** the run is in the index
