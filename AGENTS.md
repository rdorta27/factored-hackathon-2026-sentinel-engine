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

The reading order for someone arriving new is in [`docs/README.md`](docs/README.md).

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
- **PDFs** are generated with `python3 estilos/build.py` from outside the
  repository; PDFs are gitignored.
