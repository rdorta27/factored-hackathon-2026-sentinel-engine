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

For agents:

- Write new documentation in English. Do **not** reintroduce Spanish files
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
| [`docs/understand/`](docs/understand/) | The challenge, the system and the data in one read |
| [`docs/requirements/`](docs/requirements/) | Requirements with priority, owner, evidence and status |
| [`docs/build/`](docs/build/) | Areas, design rules, decisions and delivery |
| [`team/`](team/) | Plan, tasks and pending decisions |
| [`evidence/`](evidence/) | Frozen, reproducible data runs (scripts + `summary.json`) cited by the docs |
| [`openspec/`](openspec/) | OpenSpec config, specs and changes |
| [`scripts/`](scripts/) | Repository scripts; `render_flow_measurements.py` generates the flow measurements page and can verify it against a fresh run |
| [`sentinel-data-engine/`](sentinel-data-engine/) | Data pipeline (Bronze, Silver, Gold) with its own `pyproject.toml`, tests and README |
| `.claude/`, `.opencode/` | OpenSpec commands and skills for Claude Code and OpenCode (generated) |

The reading order for someone arriving new is in [`docs/README.md`](docs/README.md).

## Stack

Accepted decisions that code must follow:

- **Backend:** Python + FastAPI (decided). Loop tool (LangGraph or plain
  Python) deferred. Policy, the authenticated session and idempotency stay
  in code; no orchestrator ever sees `customer_id`. See
  [005](docs/build/decisions/005-backend.md).
- **Frontend:** a one-page chat (HTML and a little JavaScript) served by the
  same FastAPI process, talking to `POST /chat`. See
  [006](docs/build/decisions/006-frontend.md).
- **Platform:** Azure; locally it runs on Linux. See
  [001](docs/build/decisions/001-azure-platform.md).
- **Flow** (confirmed at the 9/29 review): a dispute starts as an account
  inquiry; the learned component is a prompted LLM against a keyword baseline.
  See [flow selection](docs/build/flows/03-flow-selection.md) and
  [007](docs/build/decisions/007-learned-component.md).
- Which model serves each route is still open (pending decision 10).

## Rules

- **No secrets, no data in the repo.** The repository is delivered public.
  Credentials live in `.env` (gitignored) and are shared by direct message.
  Hackathon datasets never get committed (`data/` is gitignored).
- **Commit messages** follow Conventional Commits with a mandatory two-block
  body, enforced by [`.githooks/commit-msg`](.githooks/commit-msg). Activate
  once per clone: `git config core.hooksPath .githooks`.
- **Registrations:** product and technique decisions go to
  [`docs/build/decisions/`](docs/build/decisions/) (one file each,
  use the template); team decisions go to [`team/plan.md`](team/plan.md).
  Requirements cited by a decision are listed in
  [`docs/requirements/requirements.md`](docs/requirements/requirements.md).
- **Evidence runs are write-once.** A new run goes in a new folder under
  `evidence/flows/` (e.g. `2024Q4-v3/`); never edit a committed run. Cite
  `summary.json` fields, never hand-copied numbers. Scripts read the bucket
  name from `.env` and data from the gitignored `data/`; never write the
  bucket name, account IDs or dataset rows in the repo.
- **Specs and changes** use OpenSpec (`/opsx:propose`, `/opsx:apply`, …) with
  the rules in [`openspec/config.yaml`](openspec/config.yaml): English only,
  every capability traced to a `REQ-####`.
- **No `Co-Authored-By` trailers**: the commit hook rejects them; credit people
  in the message body instead.
- **PDFs** are generated with `python3 estilos/build.py` from outside the
  repository; PDFs are gitignored.
