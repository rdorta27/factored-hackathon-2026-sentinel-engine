# final-docs-pass Specification

## Purpose
Defines the final documents pass: the repository documents match the submitted build, each number cites a field, each requirement status has its evidence, and the public repository holds no secret.

## Requirements

### Requirement: The documents match the submitted build

The documents SHALL name the model, the prompt version and the `bundle_hash` that the public link serves. Each number in the README, the metrics report and the site SHALL cite a field of a frozen `summary.json`. Traces to REQ-0030 (P0, Done) and REQ-0013 (P0, In progress).

#### Scenario: Served build

- **WHEN** `GET /api/v1/health` of the link returns a `bundle_hash`
- **THEN** the page on the public link states the same value

### Requirement: A requirement status needs its evidence

A requirement SHALL change status only when its evidence exists in the repository. The hand-written dependency chains SHALL match the statuses. Traces to REQ-0051 (P0, In progress).

#### Scenario: Evidence missing

- **WHEN** a requirement has no evidence yet
- **THEN** its status does not change

### Requirement: The public repository holds no secret, dataset row or password

The tracked files SHALL hold no credential, bucket name, dataset row or plain password. Traces to REQ-0034 (P0, Done).

#### Scenario: Scan

- **WHEN** the final scan runs on the tracked files
- **THEN** it finds none of these values, and the output goes in the commit body

### Requirement: The documentation uses one language style

Each page under `docs/` and `team/` that the review rewrites SHALL carry the ASD-STE100 header and SHALL use one term for one concept. The status words SHALL be Done, In progress and Pending. Locale tags SHALL follow BCP 47. Traces to REQ-0051 (P0, In progress).

#### Scenario: Agreed terms

- **WHEN** the review script searches a page for a synonym of an agreed term
- **THEN** the page uses the agreed term, or the review lists the page with its reason

#### Scenario: Headings and anchors

- **WHEN** a page is rewritten
- **THEN** its headings stay the same, so links with an anchor still work

#### Scenario: Out of scope pages

- **WHEN** a page is the official data dictionary or is written by a script
- **THEN** the review does not edit its content, and lists it with the reason

### Requirement: The public site matches the release

The public site SHALL show the numbers of the final `summary.json` files, the release tag and the link to the video. The page SHALL hold no password, key, bucket name or dataset row. Traces to REQ-0036 (P0, Done) and REQ-0037 (P0, Pending).

#### Scenario: Numbers

- **WHEN** the numbers test runs after the release
- **THEN** each number on the site matches a field of a frozen `summary.json`

#### Scenario: Video and release

- **WHEN** the owner has tagged the release and published the video
- **THEN** the site, the slides and the README link to both

### Requirement: The pitch matches the evidence

Each claim in the slides, the video script, the product page and the site SHALL cite a frozen `summary.json` field or a page of the repository. A simulation or a projection SHALL be labelled as such. The pitch SHALL hold no password. Traces to REQ-0036 (P0, Done) and REQ-0037 (P0, Pending).

#### Scenario: A claim without proof

- **WHEN** a claim has no cited field or page
- **THEN** the claim is fixed or removed before the video is recorded
