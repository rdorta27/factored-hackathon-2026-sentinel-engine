# Delivery

Monday 10/5, 11:59 pm (UTC-5); the video lasts 3 minutes at most. We work and deliver in **English**. The full list of deliverables is in the [overview](../overview.md#deliverables).

## Language

Everything, working material included, is written in **English from the first draft**. There is no translation pass at the end: the README, the presentation, and the video script are drafted in English from the start. `docs/` and `team/` are translated. Registered as [REQ-0051](../requirements/requirements.md).

| Piece | Language | Status | Reviewed by | Frozen |
|---|---|---|---|---|
| Repo `README.md` (the delivery link) | English | Done | Rubén | Kept in English |
| GitHub repo title and description | English | Done | Rubén | Kept in English |
| Presentation (4 to 6 slides) | Born in English | Pending | Rubén; group validates the outline Fri 10/2 | Outline Thu 10/1; reviewed Friday to Monday with the results; frozen Mon 10/5 |
| Video script | Born in English | Pending | Rubén | Script from Thu 10/1; frozen Mon 10/5 (internal deadline) |
| Demos: es-419 and pt-BR cases | Spanish and Portuguese | — | — | What the system says |
| `docs/` and `team/` | English | — | — | Translated (decision 19 closed) |
| ASD-STE100 header on each Markdown page | English | In progress | Rubén | 76 of 221 pages on 2026-10-05, counted with the command in [AGENTS.md](../../AGENTS.md#asd-ste100) |

We update it at each review, not at the end. Statuses: Pending, In progress, Done.

## Presentation

Six slides, in English, as static HTML pages: [`site/slides/deck.html`](../../site/slides/deck.html) (1280×720). Open the page in a browser. The arrow keys move between slides and `f` opens full screen. Each number comes from `site/numbers.json` with its type.

| # | Slide | Source |
|---|---|---|
| 1 | Why: the problem and its data | [problem and demand](../rationale/problem-and-demand.md), [`problem/dev-v1`](../../evidence/problem/dev-v1/summary.json) |
| 2 | What: the product and the four demo cases | [product](../product.md), [demo replay](../../sentinel-ai-core/eval/demo/replay.md) |
| 3 | How: "The AI converses. The rules decide." with the architecture drawing | [architecture](../architecture/README.md), [`architecture.json`](../../site/diagrams/architecture.json) |
| 4 | Proof: results and 0 unsafe outcomes | [evidence index](../../evidence/README.md), [metrics](metrics.md) |
| 5 | Your brand: the white label | [branding](../../sentinel-ai-core/app/branding.py) |
| 6 | Limits and roadmap, with the mocks | [mocks](../architecture/mocks.md), [README roadmap](../../README.md#roadmap) |

Build the PDFs before the submission:

```bash
python3 scripts/export_slides.py
```

The command writes `site/slides/sentinel-slides.pdf` (English), `sentinel-slides.es-419.pdf` and `sentinel-slides.pt-br.pdf`. Git ignores them. Each holds one page for each slide. Submit the English PDF.

- The why behind each choice, with the sentence for each slide, is in [rationale](../rationale/README.md).
- Each figure shows its denominator and its type: test suite, simulation or synthetic.
- We include failures and limitations. Hiding them counts against us.

## Video pitch

Mandatory, **3 minutes at most**. It shows the solution working and explains the architecture decisions. The full script, Why → What → How, with the shot list, is in [video script](video-script.md).

1. The problem, in one sentence and with one data point.
2. Demo of the **normal case** (es-419; type the es-MX line in [replay](../../sentinel-ai-core/eval/demo/replay.md)).
3. Demo of the **ambiguous case** (pt-BR; same sheet).
4. Demo of the **human case**, showing the JSON handoff.
5. A prompt injection attempt that fails.
6. Key architecture decisions (from [decisions](decisions/)).
7. Top results and limitations.

## Project site

The site and the slides are in English, Spanish (Latin America, `es-419`) and Portuguese (`pt-BR`). English is the source and the submission language ([language](#language)). The other two languages are translations for readers. `python3 scripts/localize.py` builds them from the English pages. `site/i18n/` holds the dictionaries. The ASD-STE100 rule applies to the English text only.

The static site is in `site/`. It holds plain HTML and CSS, with no build step. The workflow [`pages.yml`](../../.github/workflows/pages.yml) publishes it to GitHub Pages on each push to `main` that changes `site/`.

| Item | Detail |
|---|---|
| Numbers | `python3 scripts/site_numbers.py` writes `site/numbers.json` and the number slots of each page from the frozen `summary.json` runs |
| Check | `python3 scripts/site_numbers.py --check` and `python3 -m pytest scripts/test_site.py -q` fail when a number differs from the evidence |
| Rebuild the copies | After any change to the English text or to `site/numbers.json`, run `python3 scripts/site_numbers.py`, then `python3 scripts/localize.py`, then `python3 scripts/export_slides.py`. Run `python3 scripts/localize.py --check` to see if a copy is stale |
| Link for the judges | Use `https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/?lang=en`. It opens English whatever the language of the browser, and the browser keeps the choice. Without `?lang`, the first visit follows the browser language |
| Owner action | Open Settings, Pages. Set Source to GitHub Actions. Run the `pages` workflow once |
| Status | Site and workflow written. The first green run waits for the owner action |

## Submission email

The owner sends this email with the submission. Fill in each placeholder. Do
not put a password in the slides or the video.

- **Repository:** `<repository URL>`
- **Live link:** `<link>`
- **Slides:** `<slides URL or file>`
- **Video:** `<video URL>`

### Credentials

All judges use the same set. The cases share state between judges.

| Login | Role | Country | Password |
|---|---|---|---|
| `CUST-0001` | customer | MX | `<password>` |
| `CUST-0002` | customer | CO | `<password>` |
| `CUST-0003` | customer | AR | `<password>` |
| `ADV-0001` | advisor | MX | `<password>` |

- The plain passwords are in `deploy/judge-users/passwords.csv` on the owner's
  machine. Git ignores the file. The users file on the link holds salted hashes
  only.
- Lockout rule: after 5 failed logins for one login id or one address, the
  login answers HTTP 429. The lock lasts 15 minutes.
- The public link has no one-click entry. The documented fixture passwords do
  not work on the link.

## Submission checklist

Each row has one owner and one proof. A row stays pending until its proof exists. The checklist is [REQ-0034](../requirements/delivery.md#req-0034), [REQ-0035](../requirements/delivery.md#req-0035), [REQ-0036](../requirements/delivery.md#req-0036), [REQ-0037](../requirements/delivery.md#req-0037) and [REQ-0051](../requirements/delivery.md#req-0051).

| Item | Owner | Proof | Status |
|---|---|---|---|
| Repository | Rubén | The public repository and its [README](../../README.md) | Done |
| Deployed link | Rubén | The `GET /api/v1/health` response of the 2026-10-05 redeploy, with `bundle_hash` `2efe5962…` | Done |
| Project site | Rubén | The [Pages workflow](../../.github/workflows/pages.yml) and a green `pages` run | Pending |
| Slides PDF | Rubén | `python3 scripts/export_slides.py` writes `site/slides/sentinel-slides.pdf` | Pending |
| Video | Rubén | The video, 3 minutes at most | Pending |
| Submission email | Rubén | The email to `hackathon.admin@factored.ai`, with the [credentials block](#credentials) | Pending |
| Credentials block | Rubén | The [credentials](#credentials) table, with no real password | Done |
| GitHub Pages | Rubén | Settings, Pages, Source is GitHub Actions | Pending |
| Secret scan | Rubén | The `scan` job in CI | Done |
| Green tests | Rubén | `python3 -m pytest -q` from `sentinel-ai-core/` | Done |

## Freeze procedure

This procedure comes before gate G3. `post-freeze` task 1.1 reads it. The code freeze starts when all the code plans are merged. After the last check, nobody changes the code, the prompt, the policy, the cut-offs or the templates.

Merge before the freeze:

- Every code plan, `bank-ui` included.
- The switch decisions: `SENTINEL_LLM_PROMPT_VERSION`, `SENTINEL_LLM_CUTOFFS` and `SENTINEL_CHARGE_RANKER`.

Run the last checks in this order:

1. `python3 scripts/e2e_check.py`
2. `python3 scripts/e2e_check.py --access-check`
3. `python3 -m pytest -q` from `sentinel-ai-core/`
4. The secret scan in CI

The rule: after the last check, nobody changes the code. A change restarts the procedure.

## Gate G3 record

The owner confirmed the freeze on 2026-10-05. This record closes `post-freeze` task 1.1.

| Item | Value |
|---|---|
| Branch | `feat/post-freeze` |
| Freeze commit | `f18be6a` |
| Measured commit (sealed run) | `8ee4575` |
| `bundle_hash` of `/health` | `2efe5962f9a50d0b4fed8e7b91c10a4c7fd212d5229d74a2e58d1024ee96dfd2` |
| Local end-to-end check | Pass, `post-freeze` task 1.2 |

The `bundle_hash` of the local `/health` equals the served hash of the sealed run `2024Q4-eval-v8` (decision 018). The measured behavior is the served behavior.

Owner inputs:

| Input | Answer |
|---|---|
| (a) Freeze confirmation | Yes, the code is frozen |
| (b) Spend allowed for live model calls | USD 1 |
| (c) OK for `az` and the redeploy, and the subscription | Yes; `Azure subscription 1` (`dd53bd4a-c46b-453e-8b07-352facf6d5ad`) |
| (d) Judge sheet and users file | `deploy/judge-users/passwords.csv` and `deploy/judge-users/users.json` (generated, gitignored) |

No password is in this record.

## Release notes

Two milestones. The owner runs the tag and release commands after the final redeploy. No one pushes in the worktree.

### v0.9-demo - 2026-10-05

The demo code is merged and frozen. The link serves `router_v2` with prompt `v2` and the labelled Gold mock.

- Sealed v8 measurement: 444 cases in the main set and 92 in the top-up set (`evidence/evaluation-runs/2024Q4-eval-v8/summary.json`, `seals.v8` and `seals.v8b`). The verdict serves `router_v2`; prompt `v3` fails the zero-unsafe-wording gate and the subtype gate (decision 018, Result v8).
- Router against the baseline: the paired difference is above zero (`paired.router_v2_vs_baseline`).
- Attacks: 0 unsafe outcomes of 42 (`evidence/adversarial/20261005T014816Z/summary.json`, `totals.unsafe_outcome_rate`). The three mock-only attacks pass on the real model (`evidence/adversarial/20261005T204313Z/summary.json`).
- Live latency on the frozen build: p50 and p95 per call are `timing.per_call.p50` and `timing.per_call.p95` of `evidence/evaluation-runs/2024Q4-resolution-live-v1/summary.json`.
- `bundle_hash` of the deployed link: `2efe5962f9a50d0b4fed8e7b91c10a4c7fd212d5229d74a2e58d1024ee96dfd2`, the hash of the sealed v8 measurement.

### v1.0-submission - after the video

The delivered state: the frozen code, the repository, the public link, the site, the slides PDF and the video.

The owner runs these commands on `main`, after this branch merges and the video is published:

```bash
git tag v0.9-demo
git tag v1.0-submission
git push origin v0.9-demo v1.0-submission
gh release create v0.9-demo --title "v0.9-demo" --notes-file docs/build/delivery.md
gh release create v1.0-submission --title "v1.0-submission" --notes-file docs/build/delivery.md
```

## Handover to docs-followups-2

This record closes `post-freeze` task 6.1. The `docs-followups-2` change reads it.

| Item | Value |
|---|---|
| Freeze commit | `f18be6a` |
| `bundle_hash` of the link | `2efe5962f9a50d0b4fed8e7b91c10a4c7fd212d5229d74a2e58d1024ee96dfd2` |
| Model served | `accounts/fireworks/models/glm-5p3-flash` |
| Prompt version served | `v2` |
| Gold source served | `mock` |
| Final measurement run | `evidence/evaluation-runs/2024Q4-eval-v8` |
| Live latency run | `evidence/evaluation-runs/2024Q4-resolution-live-v1` |
| Adversarial run on the real model | `evidence/adversarial/20261005T204313Z` |
| Robustness runs | None. Tasks 3.1 to 3.3 of this plan did not run. |
| Date of the final redeploy | 2026-10-05 |

## Pending

- [x] Maximum video length: 3 minutes (confirmed 9/28)
- [ ] Recording tool
