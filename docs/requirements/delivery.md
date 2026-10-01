# Requirements: Delivery

What the evaluators receive: repository, deployed link, slides, video, limitations and the path to production. Back to the [requirements index](requirements.md), which holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0013](#req-0013) | Report data and language limits | P0 | analysis | [REQ-0012](frontend-backend.md#req-0012), [REQ-0024](analytics.md#req-0024) | Pending |
| [REQ-0030](#req-0030) | Declare what is missing | P0 | all | [REQ-0013](#req-0013), [REQ-0053](analytics.md#req-0053) | In progress |
| [REQ-0034](#req-0034) | Clean public repository | P0 | all | [REQ-0031](data-ml.md#req-0031) | In progress |
| [REQ-0035](#req-0035) | Deployed tool link | P0 | ai | [REQ-0027](non-functional.md#req-0027), [REQ-0034](#req-0034) | Pending |
| [REQ-0036](#req-0036) | Presentation, 4 to 6 slides | P0 | all | [REQ-0055](analytics.md#req-0055), [REQ-0056](non-functional.md#req-0056) | Pending |
| [REQ-0037](#req-0037) | Video pitch | P0 | all | [REQ-0009](frontend-backend.md#req-0009), [REQ-0010](frontend-backend.md#req-0010), [REQ-0011](frontend-backend.md#req-0011), [REQ-0035](#req-0035) | Pending |
| [REQ-0051](#req-0051) | Everything in English | P0 | all | [REQ-0036](#req-0036), [REQ-0037](#req-0037) | Pending |
| [REQ-0052](#req-0052) | Path to production | P0 | ai, all | [REQ-0025](non-functional.md#req-0025), [REQ-0050](analytics.md#req-0050) | In progress |

<a id="req-0013"></a>
### REQ-0013 · Report data and language limits

State openly what the data cannot support: the dataset is synthetic, Spanish only, and covers only Mexico, Colombia and Argentina, so Portuguese and other countries are untested against real material. The assumptions are listed once in the [dataset assumptions](../understand/dataset.md#assumptions).

**Priority:** P0 · **Status:** Pending · **Criterion:** Rationale · **Area:** analysis

**Source:** Problem statement: Scope · Kickoff p. 15 · Dataset summary

**Depends on:** [REQ-0012](frontend-backend.md#req-0012), [REQ-0024](analytics.md#req-0024). Coverage limits come from the language support and the breakdown.

**Evidence:** Missing: the limitations section.

<a id="req-0030"></a>
### REQ-0030 · Declare what is missing

An honest list of what the prototype lacks before real use: capacity, data, languages, deployment and remaining risks.

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** all

**Source:** Problem statement: Scope; What your solution should demonstrate 6 · Kickoff p. 15 · Help channel (9/28)

**Depends on:** [REQ-0013](#req-0013), [REQ-0053](analytics.md#req-0053). Gathers the data, language and capacity limits.

**Evidence:** Missing: the limitations section, which gathers REQ-0013 and REQ-0053.

<a id="req-0034"></a>
### REQ-0034 · Clean public repository

The repository is delivered public as `factored-hackathon-2026-sentinel-engine`, with all links sent to `hackathon.admin@factored.ai`, so it must hold no secrets, private records or restricted data.

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** all

**Source:** Kickoff p. 18

**Depends on:** [REQ-0031](data-ml.md#req-0031). No restricted data in the public repo.

**Evidence:** Proven by: the current tree has no bucket name or account id.

Missing: a final secrets and data review, and a decision on the bucket id still present in older commits.

<a id="req-0035"></a>
### REQ-0035 · Deployed tool link

A link to the running tool, with usage and spending limits. A minimal deployment is enough; cloud is not mandatory (help channel, 9/28).

**Priority:** P0 · **Status:** Pending · **Criterion:** AI Engineering · **Area:** ai

**Source:** Kickoff p. 18 · Help channel (9/28)

**Depends on:** [REQ-0027](non-functional.md#req-0027), [REQ-0034](#req-0034). A public link needs the session and a clean repo.

**Evidence:** Missing: the deployment and its link.

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

**Evidence:** Proven by: the [path to production](../architecture/specification.md#path-to-production).

Missing: monitoring (REQ-0050) and handoff delivery (decision 28).
