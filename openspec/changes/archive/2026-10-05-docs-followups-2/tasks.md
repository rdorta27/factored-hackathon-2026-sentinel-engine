---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Tasks

Areas: [analysis](../../../docs/build/areas/analysis.md). Paths are relative to the repository root. No code changes. If a fix needs code, stop and tell the owner.

Starts after `post-freeze` and `release` are merged. Merge `origin/main` first. Read `team/pending-decisions.md` and `docs/build/delivery.md` before you start.

**Mode.** Every task is automatic. No task waits for the owner or for another plan. The work that needs the tags, the video or the deployed site is in the `video` change. **Priority (the submission is due on 2026-10-05, 11:59 PM COT).** Required: 6.1 (the scan for secrets in the public repository) and 7.1 to 7.5 (the slides, the script, the product page, the README pitch, the claims table and the three PDFs). Next: 1.1 to 1.3, 2.1, 2.2, 3.1 and 3.2. Cut first: group 5 (the review of all pages), 4.1 to 4.4, 6.2 and 6.3. Defaults, set by the owner on 2026-10-05: archive the finished plans in task 4.2, and keep a superseded page with a note at the top (task 5.5), never delete it.

## 1. Public link and architecture pages

- [x] 1.1 Update `docs/rationale/public-link.md` and the consequences of decision 019: the live revision and its date, the model and prompt version served, the `bundle_hash` of `GET /api/v1/health`, and the state on the share. Evidence: the two files and the health output in `docs/build/delivery.md`.
- [x] 1.2 Update `docs/architecture/what-is-real.md` and `docs/architecture/mocks.md`: the model that the link serves, the attack cases that now run on the real model, the new runs, and the login rule of `judge-access` (no passwordless entry, credentials in the submission email). Evidence: the two files.
- [x] 1.3 Check the README: the live link, the deployment line, the `## Limitations` and `## Roadmap` sections, and the demo credentials note. Evidence: the diff.

## 2. Numbers and evidence

- [x] 2.1 Regenerate the metrics report if a run changed. Check that each number in the README, the metrics report and `site/` cites a field of a `summary.json`. Evidence: the numbers test of the site and a search for hand-copied values.
- [x] 2.2 Check `evidence/README.md`: each run has its status (current or superseded), its data type and its requirements. Include the final measurement, the robustness runs, the live latency run, the resolution gap run and the cut-off diagnosis. Evidence: the file.

## 3. Requirements

- [x] 3.1 Change the status of a requirement only where its evidence exists now: REQ-0013, REQ-0022, REQ-0030, REQ-0035, REQ-0036, REQ-0051, REQ-0052 and REQ-0055. REQ-0037 (the video) changes in the `video` change. Evidence: `docs/requirements/`.
- [x] 3.2 Update the status counts and the hand-written chains in `docs/requirements/requirements.md`. Remove each "Planned by" line whose work is done. Evidence: the file.

## 4. Plans and team

- [x] 4.1 Run `openspec validate --all`. Fix each error in a document. Evidence: the output in the commit body.
- [x] 4.2 Archive the finished plans, in this order: `eval-v8`, `evidence-hardening`, `demo-clarity`, `judge-access`, `live-ops`, `pitch-site`, `release`, `post-freeze` and, last, this change. Sync the specs. Do not archive the `video` change: it runs later. Evidence: `openspec/changes/archive/`. The archive holds the ten complete changes, `eval-v8-measure` and `docs-followups` included, each with its main spec. The links to a moved plan point to the archive. `openspec validate --all` passes. This change goes last.
- [x] 4.3 Update `team/tasks.md` (the status of each task), `team/plan.md` (the schedule and the decisions) and `team/pending-decisions.md` (close each open row). Evidence: the three files. The three pages follow the standard now, and `team/pending-decisions.md` has no open row.
- [x] 4.4 Run `scripts/check_spec_citations.py` and fix each citation that differs from `requirements.md`. Evidence: the script prints no difference.

## 5. Full review of `docs/` and `team/`

On 2026-10-05 on the branch `feat/docs-followups`, `docs/` holds 78 pages (57 with the ASD-STE100 header, 21 without) and `team/` holds 7 pages (none with the header). A page with the header can still drift. The review covers all 85 pages. The owner asked for this review.

Rules for the whole group: keep the headings of a page that you rewrite, because other pages link to their anchors. Put the header on a page only when you rewrite it in full, and set `last_reviewed` to the date of the pass. Keep code identifiers, field paths, `REQ-####` ids, decision numbers and dataset values as they are. Keep banking terms in Spanish or Portuguese in the original, with an English explanation the first time. Never delete a page. Write each change in a small commit for one folder.

Out of scope: `docs/data/reference/latam-bank-data-dictionary.md` (official source material, do not edit its content), the Spanish and Portuguese terms in the locale glossary files, and the block of `team/chat-manual-tests.md` between the `manual-test-replay` markers (a script writes it). If a script generates a page (for example the reports in `docs/reports/`), change the generator template, not the output.

- [x] 5.1 Write `scripts/check_docs.py`. It prints, for each page under `docs/` and `team/`: the header status, the date of `last_reviewed`, sentences of more than 25 words, likely passive verbs, bare locale tags (`ES`, `PT`), and the use of a synonym of an agreed term (handoff, cut-off, held-out, baseline, simulation, mock). It changes nothing. Evidence: `scripts/check_docs.py`, `scripts/test_check_docs.py` (nine tests pass) and the summary count: 95 pages, 87 with the header, 77 long sentences, 243 likely passives, 0 bare locale tags and 74 synonyms.
- [x] 5.2 Write the list of agreed terms from `AGENTS.md` and `docs/glossary/glossary.en-us.md`: one term for one concept. Search the pages for the synonyms. Add a missing agreed term to the English glossary. Evidence: the glossary and the search output in the commit body. The glossary holds the six terms. The script found no missing term.
- [x] 5.3 Review and rewrite `docs/build/` (areas, flows, decisions, cost, ROI, delivery, metrics and the rest), then `docs/architecture/` and `docs/rationale/`. One commit for each folder. Evidence: the commits and the output of task 5.1 for these folders.
- [x] 5.4 Review and rewrite `docs/requirements/`, `docs/data/` (except the official dictionary), `docs/overview.md`, `docs/README.md`, `docs/glossary/glossary.en-us.md` and `docs/reports/`. Evidence: the commits and the output of task 5.1.
- [x] 5.5 Review and rewrite the seven pages of `team/`: `plan.md`, `tasks.md`, `pending-decisions.md`, `chat-manual-tests.md`, `component-status.md`, `chat-behavior-plan.md` and `router-v3-plan.md`. Make each status agree with `docs/requirements/requirements.md` and with the plans. If a page is superseded, add a note at the top with the page that replaces it. Never delete a page. Evidence: the commits.
- [x] 5.6 Check the consistency of the whole set: each `REQ-####` and each decision number resolves to a card or a file; the status words are only Done, In progress and Pending; locale tags are BCP 47 (`en-US`, `es-MX`, `es-CO`, `es-AR`, `es-419`, `pt-BR`); each number cites a field. Run `scripts/check_links.py` and `scripts/check_spec_citations.py`. Evidence: the output in the commit body. The 57 `REQ-####` ids and the 30 decision numbers resolve. The status words are the three. The locale tags are BCP 47. The numbers test passes. The two scripts print no difference.
- [x] 5.7 List the pages in ASD-STE100 with `grep -rl '^style: ASD-STE100' --include=*.md . | grep -v AGENTS.md`. List each page without the header and its reason (out of scope, generated, or the owner kept it). Evidence: the two lists in the commit body.

## 6. Repository hygiene and submission

- [x] 6.1 Search the slides, `site/` and the video script for a password, key or bucket name (from `judge-access` 4.3). Scan the tracked files for secrets and data: API keys, the bucket name, account ids, dataset rows, `.env` files and plain passwords outside the documented local fixtures. Use fixed `git grep` commands and `git ls-files`. Evidence: the commands and the empty output in the commit body.
- [x] 6.2 Compare the delivery checklist in `docs/build/delivery.md` with the real items: the repository name (`factored-hackathon-2026-[team]`), the public link, the slides, the video and the email template with the credentials block. Do not write a real password. Mark the rows of the video, the tags and the email as owned by the `video` change. Evidence: the checklist with each row checked or marked.
- [x] 6.3 Write the exact `git tag v1.0-submission` and `gh release create` commands in `docs/build/delivery.md`. The owner runs them. Evidence: the file.

## 7. Pitch and presentation (first pass)

This pass runs right after `release` and **before the video is recorded**. It brings the slides, the video script, the product page and the README pitch to the final state. The links that need the tags, the video and the deployed site are in the `video` change (it runs after the owner tags and publishes). Only content and links change. The `bundle_hash` does not change.

- [x] 7.1 Update the six slides in `site/slides/` to the final state. The site and the slides exist in English, `es-419` and `pt-BR`: change the English text first, add each new text to both dictionaries in `site/i18n/`, and run `python3 scripts/localize.py` and `python3 scripts/localize.py --check`. Bring the slides to the final state: numbers from `site/numbers.json` (never typed by hand), the final public link, the build line (model, prompt version, short `bundle_hash`), the wording of the results (the intent gain and the resolution ceiling of 16 of 56), the slide on limits and mocks, the architecture drawing, and the line that the credentials come in the submission email. No password on any slide. Evidence: the diff and the numbers test.
- [x] 7.2 Update the video script (Why, What, How) and its shot list to the final build. Expand shot 6 so that the advisor view shows what it offers: the list of tickets (reason, country, language, age) and the detail (the request, the verified facts, the actions that the system tried, the evidence with the rule id, the open questions and the trace of the turn). Use the high-amount case, which hands off with no insistence. Add one sentence in the limits part: the system does not learn in production; the outcomes of advisor handoffs are the feedback dataset of the roadmap, not built. The voice is the owner's own voice, in English, with no AI voice-over (organizers' rule of 2026-10-05). Update the shot list to the final build: the demo steps on the redeployed link, the final numbers, the architecture drawing, and no password or key on screen. Evidence: the script in `docs/build/delivery.md`.
- [x] 7.3 Update `docs/product.md` and the pitch lines of the README (tagline, results, links) to the final numbers and links. Evidence: the diff.
- [x] 7.4 Write a table of claims to evidence: each claim in the slides, the script, the product page and the site, with the `summary.json` field or the page that proves it. Fix or remove a claim that has no proof. Label simulations and projections as such. Evidence: the table in the commit body.
- [x] 7.5 Export the slides with `python3 scripts/export_slides.py` and check that the three PDFs (English, `es-419`, `pt-BR`) have six pages each and match `site/slides/`. Evidence: the PDF names and the page counts in the commit body.
