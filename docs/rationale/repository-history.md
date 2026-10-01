# Repository history

## Choice

An early commit named the hackathon's data bucket. The current tree reads it from `.env`; we did **not** rewrite git history to remove the old mention.

## Why

- **A bucket name is not a credential.** Access depends on the cloud permissions, not on knowing the name.
- **Rewriting history means a force push,** which already disconnected the team's branches once.
- **Two checks close it instead:** a scan of the whole history (not only the current tree) for keys and data, and confirmation that the bucket refuses anonymous listing and reading.

## Alternatives rejected

- **Purge with `git filter-repo` and force push:** every collaborator re-clones, open branches break, and the host may keep old commits anyway.

## In production

A pre-commit check that rejects bucket URLs, account ids and key patterns, so the case does not repeat.

## On the slide

Not a slide of its own; one line in limitations: "Old history mentions the data bucket by name; keys and data were checked across the whole history, and the bucket is not public." Use this line only after both checks pass (pending: the history scan and the confirmation from the data owner).
