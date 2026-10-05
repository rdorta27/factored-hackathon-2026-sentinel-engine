---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

The organizers said that good GitHub practice earns easy points: feature branches, small and frequent pull requests, and clear commits with tagged versions. The repository has the branches and the commits. It has **no tags and no releases**, no changelog, and no page that tells a reader how the team works. The submission also needs a last checklist: the repository link, the deployed link, the slides, the video and the email to the organizers.

## What Changes

- **A changelog** `CHANGELOG.md`, in plain English, with one entry per merged pull request and one section per milestone.
- **A "How we work" page** `CONTRIBUTING.md`: the branch and pull request flow, the commit rules, the plan flow (OpenSpec) and the evidence rules. It copies the rules of `AGENTS.md` for a human reader and links to them.
- **A tag plan.** Two tags: `v0.9-demo` when the code of the demo is merged, and `v1.0-submission` after the final deploy. The commands and the release notes are written. The owner runs them, because they need a push.
- **A submission checklist** in `docs/build/delivery.md`: the repository name, the deployed link, the slides as a PDF, the video, the email address, the Pages setting, the secret scan, and a green test run.
- **A freeze procedure:** the list of what must be merged, the order of the last checks (`scripts/e2e_check.py`, the test suites and the secret scan) and the rule that nobody changes code after the final check.
- **A last review of the README:** the links work, the numbers cite their fields, and the limits section is current.

## Capabilities

### New Capabilities
- `release-notes`: the changelog, the tags and the submission checklist.

### Modified Capabilities
(none)

## Impact

- `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/build/delivery.md`, `README.md`, REQ-0034, REQ-0035 and REQ-0051 evidence.
- No code changes.

## Non-goals

- Pushing, opening pull requests, creating tags or sending the email. The owner does all of these.
- Rewriting the history of the repository.
