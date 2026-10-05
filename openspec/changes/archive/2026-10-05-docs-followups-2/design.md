---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Design

## Order

This change starts when `docs-followups`, `eval-v8`, `evidence-hardening`, `demo-clarity`, `judge-access`, `live-ops`, `pitch-site`, `post-freeze` and `release` are merged. It is the last change before the owner tags the release. It takes over the closing documents that `post-freeze` listed in its group 6.

## Decisions

| Topic | Choice | Reason |
|---|---|---|
| One pass at the end | One change, small commits by topic | The owner can review each topic and open small pull requests |
| Statuses | Change a requirement status only with evidence | A wrong "Done" costs trust |
| Numbers | Cite fields, do not copy numbers | The rule of the evidence index |
| Scan | A script or a fixed list of `git grep` commands | The result is repeatable and goes in the commit body |
| Review order | Script first, then one folder at a time | The script gives the count of findings. Small commits let the owner review each folder |
| What a rewrite keeps | Headings, anchors, identifiers, ids and dataset values | Other pages and the specs link to them |
| Generated pages | Change the generator, not the page | The next run would overwrite a hand edit |
| Archive | The owner chooses the moment | Archiving merges deltas into the main specs |
| Pitch and site | Two passes: slides and script before the video, links after the tags and the video | The script must be final before recording. The tag, the release and the video exist only later |
| Last archive | This change archives itself last | The archive step must see the final state |

## Risks

| Risk | Control |
|---|---|
| A page cites a number that moved | The numbers test of the site and a search for hand-copied values |
| A fix needs code | Stop and tell the owner. Reopen gate G3 |
| A late conflict with another branch | Merge `origin/main` first. Keep commits small |
