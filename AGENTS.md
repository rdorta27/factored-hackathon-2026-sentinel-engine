# AGENTS.md

Guidance for anyone working in this repository — human or AI agent.

## Language

The hackathon is judged in English and the whole repository is written in
English, including working documents.

| Where | Language | Why |
|---|---|---|
| [`team/`](team/) | English | Internal planning, kept submission-ready. |
| [`docs/`](docs/) | English | Working copy the team edits daily. |
| Root [`README.md`](README.md), slides, video script | English | The deliverable the evaluators read. |

**Rule of thumb: everything is drafted in English from the first draft.**
There is no translation pass at the end. Tracked as REQ-0051; the status table lives in
[`docs/build/delivery.md`](docs/build/delivery.md#language).

**All documentation is written in simplified technical English
(ASD-STE100).** This applies to every new or edited Markdown file: README,
`docs/`, `team/`, `evidence/` READMEs, OpenSpec artifacts, decisions, commit
bodies and PR descriptions. The rules that matter most:

- One idea per sentence. At most 20 words in a procedure step and 25 words
  in a description.
- Active voice and present tense. Write "the router labels the intent", not
  "the intent is labelled by the router".
- One instruction per sentence, in the imperative: "Set the variable."
- One term for one concept. Do not use synonyms for variety (for example,
  always "handoff", never also "transfer" and "escalation" for the same thing).
- Simple, common words. Do not use idioms, phrasal verbs with a vague meaning,
  or noun clusters longer than three words.
- Tables and lists instead of long paragraphs.
- Keep exact technical names as they are: code identifiers, field paths,
  REQ ids, decision numbers and dataset values.
- Keep the headings of a page you rewrite. Other pages link to their anchors.

**Mark each file written or rewritten in ASD-STE100** with this frontmatter
at the top of the file, before the title. Set `last_reviewed` to the date of
the last full review of the file in ASD-STE100:

```yaml
---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---
```

A file without this frontmatter is not yet in ASD-STE100. When you rewrite
it, add the frontmatter. Do not add the frontmatter to a file that you only
edit in part. To list the files that are done:
`grep -rl '^style: ASD-STE100' --include=*.md .`


For agents:

- Write new documentation in English and in ASD-STE100. When you edit a
  page, rewrite the parts you touch in ASD-STE100. Do **not** reintroduce Spanish files
  under `docs/` or `team/` unless explicitly asked.
- Do **not** write new documentation in Portuguese. The system must answer in
  Spanish and Portuguese; our own writing stays in English.
- Banking terms, acronyms and dialogue examples in Spanish or Portuguese are
  kept in the original with an English explanation on first use; locale
  vocabulary lives in [`docs/understand/glossary/`](docs/understand/glossary/).
- New English text is expected whenever it belongs to a deliverable.
- Locales are written as BCP 47 tags: `en-US`, `es-MX`, `es-CO`, `es-AR`,
  `pt-BR`. When something applies to Spanish across the three countries, use
  `es-419` (Latin American Spanish). Do not write `ES`/`PT` alone.

## Layout

| Path | What it holds |
|---|---|
| [`docs/architecture/`](docs/architecture/) | System Architecture, Demo Architecture, their specification, and [what is real](docs/architecture/what-is-real.md) (real, mock, synthetic, team-generated, simulation, projection) |
| [`docs/rationale/`](docs/rationale/README.md) | Why each choice, with an evidence table and the slide sentence |
| [`docs/understand/`](docs/understand/) | The challenge and the data in one read; [`reference/`](docs/understand/reference/) holds the official data dictionary |
| [`docs/requirements/`](docs/requirements/) | Requirements: [`requirements.md`](docs/requirements/requirements.md) is the index (sources, status, dependencies); one file per type holds the cards with description and evidence |
| [`docs/build/`](docs/build/) | Areas, design rules, decisions and delivery |
| [`team/`](team/) | Plan, tasks and pending decisions |
| [`evidence/`](evidence/README.md) | Frozen, reproducible runs (scripts + `summary.json`) cited by the docs. [`evidence/README.md`](evidence/README.md) indexes every run with its status and data type |
| [`openspec/`](openspec/) | OpenSpec config, specs and changes |
| [`scripts/`](scripts/) | Repository scripts; `render_flow_measurements.py` generates the flow measurements page and can verify it against a fresh run |
| [`sentinel-data-engine/`](sentinel-data-engine/) | Data pipeline (Bronze, Silver, Gold). Natalia. |
| [`sentinel-ai-core/`](sentinel-ai-core/) | Charge-inquiry loop, policy engine, the page (customer chat and advisor view) and the API under `/api/v1`. Owners in [team/plan.md](team/plan.md#folders). |
| [`sentinel-login/`](sentinel-login/) | Original demo page kept as a reference; not a backend and not served ([009](docs/build/decisions/009-demo-ui-and-advisor-view.md)). |
| `.claude/`, `.opencode/` | OpenSpec commands and skills for Claude Code and OpenCode (generated) |

The reading order for someone arriving new is in [`docs/README.md`](docs/README.md).

## Stack

Accepted decisions that code must follow:

- **Backend:** Python + FastAPI (decided). Loop tool (LangGraph or plain
  Python) deferred. Policy, the authenticated session and idempotency stay
  in code; no orchestrator ever sees `customer_id`. See
  [005](docs/build/decisions/005-backend.md).
- **Frontend:** a one-page chat (HTML and a little JavaScript) served by the
  same FastAPI process, talking to `POST /api/v1/chat`. See
  [006](docs/build/decisions/006-frontend.md).
- **Platform:** Azure; locally it runs on Linux. See
  [001](docs/build/decisions/001-azure-platform.md).
- **Flow** (confirmed at the 9/29 review): a dispute starts as an account
  inquiry; the learned component is a prompted LLM intent router against a keyword baseline.
  See [flow selection](docs/build/flows/03-flow-selection.md) and
  [007](docs/build/decisions/007-learned-component.md).
- **Router model:** GLM 5.3 Flash on Fireworks AI on both routes, with the
  keyword baseline as the per-turn fallback. See
  [016](docs/build/decisions/016-router-models.md).

## Rules

- **No secrets, no data in the repo.** The repository is delivered public.
  Credentials live in `.env` (gitignored) and are shared by direct message.
  Hackathon datasets never get committed (`data/` is gitignored). The one
  reference exception is the official data dictionary in
  [`docs/understand/reference/`](docs/understand/reference/): schema, not rows.
- **Commit messages** follow Conventional Commits with a mandatory two-block
  body, enforced by [`.githooks/commit-msg`](.githooks/commit-msg). Activate
  once per clone: `git config core.hooksPath .githooks`.
- **Registrations:** product and technique decisions go to
  [`docs/build/decisions/`](docs/build/decisions/) (one file each,
  use the template); team decisions go to [`team/plan.md`](team/plan.md).
  Requirements cited by a decision are listed in
  [`docs/requirements/requirements.md`](docs/requirements/requirements.md).
- **Label what is real.** Every component, data source and number is real,
  mock, synthetic, team-generated, simulation or projection, as defined in
  [what is real](docs/architecture/what-is-real.md). Never present a
  simulation or a projection as a production measurement.
- **Evidence runs are write-once.** A new run goes in a new folder under
  `evidence/flows/` (e.g. `2024Q4-v3/`) or `evidence/adversarial/`; never edit
  a committed run. Cite `summary.json` fields, never hand-copied numbers. Add each new run to
  [`evidence/README.md`](evidence/README.md) with its status (current or
  superseded), data type and requirements.
  Scripts read the bucket name from `.env` and data from the gitignored
  `data/`; never write the bucket name, account IDs or dataset rows in the repo.
- **Adversarial evidence** is produced by the test suite, not by hand. Run
  `SENTINEL_WRITE_EVIDENCE=1 python -m pytest tests/adversarial -q` from
  `sentinel-ai-core/` to write one new run under
  `evidence/adversarial/<run-id>/summary.json`. The counts are derived from the
  real pytest outcomes; the `unsafe_outcome_rate` denominator is every attack
  attempted. See [`sentinel-ai-core/tests/adversarial/summary.py`](sentinel-ai-core/tests/adversarial/summary.py).
- **Specs and changes** use OpenSpec (`/opsx:propose`, `/opsx:apply`, …) with
  the rules in [`openspec/config.yaml`](openspec/config.yaml): English only,
  every capability traced to a `REQ-####`.
- **No `Co-Authored-By` trailers**: the commit hook rejects them; credit people
  in the message body instead.
- **PDFs** are generated with `python3 estilos/build.py` from outside the
  repository; PDFs are gitignored.
