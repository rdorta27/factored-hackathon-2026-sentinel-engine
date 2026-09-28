# AGENTS.md

Guidance for anyone working in this repository — human or AI agent.

## Language

The hackathon is judged in English, but the team writes in Spanish because it
is faster. Both are fine here; they apply to different things.

| Where | Language | Why |
|---|---|---|
| [`team/`](team/) | Spanish | Internal planning. Never submitted as-is. |
| [`docs/`](docs/) | Spanish | Working copy the team edits daily. |
| Root [`README.md`](README.md), slides, video script | English | The deliverable the evaluators read. |

**Rule of thumb: deliverables are drafted in English from the first draft;
working documents are drafted in Spanish.** There is no translation pass at
the end. The README, the slides and the video script are written in English as
they are created. Tracked as REQ-0051; the status table lives in
[`docs/construir/entrega.md`](docs/construir/entrega.md#idioma).

For agents:

- Do **not** translate existing documents under `docs/` or `team/` unless
  explicitly asked — they are working copies and are never submitted.
- Do **not** write new documentation in Portuguese. The system must answer in
  Spanish and Portuguese; our own writing stays in Spanish.
- New English text is expected whenever it belongs to a deliverable.

## Layout

| Path | What it holds |
|---|---|
| [`docs/entender/`](docs/entender/) | The challenge, the system and the data in one read |
| [`docs/requerimientos/`](docs/requerimientos/) | Requirements with priority, owner, evidence and status |
| [`docs/construir/`](docs/construir/) | Areas, design rules, decisions and delivery |
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
  [`docs/construir/decisiones/`](docs/construir/decisiones/) (one file each,
  use the template); team decisions go to [`team/plan.md`](team/plan.md).
  Requirements cited by a decision are listed in
  [`docs/requerimientos/requerimientos.md`](docs/requerimientos/requerimientos.md).
- **PDFs** are generated with `python3 estilos/build.py` from outside the
  repository; PDFs are gitignored.
