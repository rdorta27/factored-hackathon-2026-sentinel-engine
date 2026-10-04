---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Repository history

## Choice

An early commit names the data bucket of the hackathon. The current tree reads the name from `.env`. We did **not** rewrite the git history to remove the old mention.

## Why

- **A bucket name is not a credential.** Access depends on cloud permissions, not on the name.
- **A history rewrite needs a force push.** A force push already disconnected the team branches once.
- **Two checks close the risk:**
  1. A scan of the full history, not only the current tree, for keys and data.
  2. A confirmation that the bucket refuses anonymous list and read.

## Evidence

| Check | Where | Result |
|---|---|---|
| History scan for keys and dataset rows | [security: history review](../build/security.md#history-review-req-0034-101) | no keys and no dataset rows |
| Bucket access | confirmed by the data owner | the bucket is private |

## Alternatives rejected

- **Purge with `git filter-repo` and force push.** Every collaborator must clone again. Open branches break. The host can keep old commits.

## In production

A pre-commit check refuses bucket URLs, account ids and key patterns.

## On the slide

No slide of its own. One line in the limits: "Old history names the data bucket. We checked the full history for keys and data, and the bucket is not public."
