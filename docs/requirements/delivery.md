# Requirements: Delivery

What the evaluators receive: repository, deployed link, slides, video, limitations and the path to production. Back to the [requirements index](requirements.md), which holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0013](#req-0013) | Report data and language limits | P0 | analysis | [REQ-0012](frontend-backend.md#req-0012), [REQ-0024](analytics.md#req-0024) | In progress |
| [REQ-0030](#req-0030) | Declare what is missing | P0 | all | [REQ-0013](#req-0013), [REQ-0053](analytics.md#req-0053) | In progress |
| [REQ-0034](#req-0034) | Clean public repository | P0 | all | [REQ-0031](data-ml.md#req-0031) | Done |
| [REQ-0035](#req-0035) | Deployed tool link | P0 | ai | [REQ-0027](non-functional.md#req-0027), [REQ-0034](#req-0034) | Done |
| [REQ-0036](#req-0036) | Presentation, 4 to 6 slides | P0 | all | [REQ-0055](analytics.md#req-0055), [REQ-0056](non-functional.md#req-0056) | Pending |
| [REQ-0037](#req-0037) | Video pitch | P0 | all | [REQ-0009](frontend-backend.md#req-0009), [REQ-0010](frontend-backend.md#req-0010), [REQ-0011](frontend-backend.md#req-0011), [REQ-0035](#req-0035) | Pending |
| [REQ-0051](#req-0051) | Everything in English | P0 | all | [REQ-0036](#req-0036), [REQ-0037](#req-0037) | Pending |
| [REQ-0052](#req-0052) | Path to production | P0 | ai, all | [REQ-0025](non-functional.md#req-0025), [REQ-0050](analytics.md#req-0050) | In progress |

<a id="req-0013"></a>
### REQ-0013 · Report data and language limits

State openly what the data cannot support: the dataset is synthetic, Spanish only, and covers only Mexico, Colombia and Argentina, so Portuguese and other countries are untested against real material. The assumptions are listed once in the [dataset assumptions](../understand/dataset.md#assumptions).

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** analysis

**Source:** Problem statement: Scope · Kickoff p. 15 · Dataset summary

**Depends on:** [REQ-0012](frontend-backend.md#req-0012), [REQ-0024](analytics.md#req-0024). Coverage limits come from the language support and the breakdown.

**Evidence:** Proven by: the [dataset assumptions](../understand/dataset.md#assumptions) and [rationale](../rationale/data-assumptions.md): synthetic data, Spanish only, accounts only in México, Colombia and Argentina, and Mexican accounts only in USD.

Proven by (also): the README [limitations](../../README.md#limitations) section.

The three demo pt-BR lines were written by grok-4.7 and back-translated by DeepSeek V4.1 Flash ([`eval/review/demo-pt-br.md`](../../sentinel-ai-core/eval/review/demo-pt-br.md)): no native speaker. A Colombian teammate accepted the three es-CO lines on 2026-10-02 after the normal line named the peso as mexicano. The same model found no drift on es-MX and es-AR; nobody on the team speaks those varieties. A 2% replay of `customer_text` on the development side of the 70/30 time split (held-out cut 2025-07-01) is in [`evidence/transcript-chats/20261002T144836Z/summary.json`](../../evidence/transcript-chats/20261002T144836Z/summary.json): 280 handoffs out of 280, and 2 distinct prefixes. The engine data directory has no transcript files, so the read was the analysis working copy; no customer data was copied into the repo. The local files are the 2024Q4 window only, so no held-out row was present to exclude. The 14,023 transcripts are two templates, not customer language. Pix hands off. `extrato` and `fatura` are not marked out of scope, because the sealed set uses them inside charge inquiries.

Missing: the limits on the slides, including the limits fixed in [018](../build/decisions/018-evaluation-acceptance.md): model-written and model-reviewed cases with no human or native-speaker review, and no strict equivalence between variants.

<a id="req-0030"></a>
### REQ-0030 · Declare what is missing

An honest list of what the prototype lacks before real use: capacity, data, languages, deployment and remaining risks.

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** all

**Source:** Problem statement: Scope; What your solution should demonstrate 6 · Kickoff p. 15 · Help channel (9/28)

**Depends on:** [REQ-0013](#req-0013), [REQ-0053](analytics.md#req-0053). Gathers the data, language and capacity limits.

**Evidence:** Proven by: the README [limitations](../../README.md#limitations) section (data, languages, model, state, privacy, safety evidence, deployment) and the [sizing](../sizing_capacity.md) (REQ-0053).

Missing: the same limits on the slides.

<a id="req-0034"></a>
### REQ-0034 · Clean public repository

The repository is delivered public as `factored-hackathon-2026-sentinel-engine`, with all links sent to `hackathon.admin@factored.ai`, so it must hold no secrets, private records or restricted data.

**Priority:** P0 · **Status:** Done · **Criterion:** Rationale · **Area:** all

**Source:** Kickoff p. 18

**Depends on:** [REQ-0031](data-ml.md#req-0031). No restricted data in the public repo.

**Evidence:** Proven by: the current tree holds no bucket name or account id; `gitleaks git --redact` over the full history reports 0 findings across the 246 commits, with no AWS key shapes, no private key material and no real passwords; no dataset rows were ever committed (no `.csv`, `.parquet`, `.duckdb` or database blob, and no `data/` or `raw/` folder, in any commit); `.gitignore` covers `data/`, `.env` and the local data formats; and `.github/workflows/gitleaks.yml` scans the commits each push and pull request adds, so a new secret is caught as it enters the repository. The review and its blind spot are recorded in [security](../build/security.md#history-review-req-0034-101).

Accepted residual risk, documented: the dataset bucket name is visible in commits before `d070faa`. The bucket is private, no credentials were exposed, and the team decided not to rewrite history. The name is public; access is not.

<a id="req-0035"></a>
### REQ-0035 · Deployed tool link

A link to the running tool, with usage and spending limits. A minimal deployment is enough; cloud is not mandatory (help channel, 9/28).

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Kickoff p. 18 · Help channel (9/28)

**Depends on:** [REQ-0027](non-functional.md#req-0027), [REQ-0034](#req-0034). A public link needs the session and a clean repo.

**Evidence:** Pending: redeploy with router_v2 (`--min-replicas 1`, the model variables from `.env`) and a remote check of `GET /api/v1/health` (model, prompt version) and of the three demo cases. Proven by, before that redeploy: the live link at `https://sentinel-engine.ambitiousmoss-1416426d.eastus.azurecontainerapps.io`, deployed 10/02 from [deploy/azure](../../deploy/azure/deploy.sh) under [019](../build/decisions/019-azure-container-apps.md) (Hugging Face dropped its free Docker tier, so [012](../build/decisions/012-public-deployment.md) is superseded). Verified remotely on 10/02: `GET /api/v1/health` returns `{"status":"ok","gold_source":"mock","state_backend":"sqlite","reference_date":"2026-06-17"}`, the page and branding load, `CUST-0001` logs in and creates a dispute (201), and `ADV-0001` sees the handoffs. Usage and spending limits: hosting sits inside the Azure monthly free grant plus about USD 0.08/day for the registry, all within the USD 200 trial credit ([cost](../build/cost.md)). The 10/02 hardening changes the deploy to one replica (SQLite is per instance), a non-root user with state under `/tmp/sentinel`, a container healthcheck and a health route that answers 503 when the state store fails; the image was built and run locally, but the live link has not been redeployed from this branch yet.

<a id="req-0036"></a>
### REQ-0036 · Presentation, 4 to 6 slides

A short slide deck describing the tool, part of the mandatory submission.

**Priority:** P0 · **Status:** Pending · **Criterion:** Rationale · **Area:** all

**Source:** Kickoff p. 18

**Depends on:** [REQ-0055](analytics.md#req-0055), [REQ-0056](non-functional.md#req-0056). Slides present metrics and trade-offs.

**Evidence:** Missing: the slides. [Script](../build/delivery.md#presentation).

<a id="req-0037"></a>
### REQ-0037 · Video pitch

A short, mandatory video (3 minutes at most) that shows the working solution and explains the core architecture decisions.

**Priority:** P0 · **Status:** Pending · **Criterion:** Rationale · **Area:** all

**Source:** Kickoff p. 18

**Depends on:** [REQ-0009](frontend-backend.md#req-0009), [REQ-0010](frontend-backend.md#req-0010), [REQ-0011](frontend-backend.md#req-0011), [REQ-0035](#req-0035). The video shows the three demo cases on the deployed tool.

**Evidence:** Missing: the video. [Script](../build/delivery.md#video-pitch).

<a id="req-0051"></a>
### REQ-0051 · Everything in English

The README, slides, video script, `docs/` and `team/` are written in English, since the hackathon is judged in English.

**Priority:** P0 · **Status:** Pending · **Criterion:** Rationale · **Area:** all

**Source:** Own: [language](../build/delivery.md#language)

**Depends on:** [REQ-0036](#req-0036), [REQ-0037](#req-0037). Language check covers the slides and video script.

**Evidence:** Missing: the [pre-submission check](../build/delivery.md#language).

<a id="req-0052"></a>
### REQ-0052 · Path to production

A credible account of how the prototype would be deployed, scaled, monitored and secured, and what changes from the prototype.

**Priority:** P0 · **Status:** In progress · **Criterion:** AI Engineering / Rationale · **Area:** ai, all

**Source:** Help channel (9/28) · Kickoff p. 15

**Depends on:** [REQ-0025](non-functional.md#req-0025), [REQ-0050](analytics.md#req-0050). Path to production includes monitoring.

**Evidence:** Proven by: the [path to production](../architecture/specification.md#path-to-production). The demo's monitoring path is one JSON line per turn on standard output (`SENTINEL_LOG_STDOUT`), which Container Apps forwards to Log Analytics; the file and the query text land under [REQ-0035](#req-0035) after the redeploy. OpenTelemetry remains the production path.

Missing: alerts by country (REQ-0050). Handoff delivery is specified ([015](../build/decisions/015-handoff-delivery.md)).
