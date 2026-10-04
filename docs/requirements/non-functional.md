# Requirements: Non-functional

How the system behaves: security, privacy, reliability, observability and reproducibility. Back to the [requirements index](requirements.md), which holds the sources, the classification, the status counts and the dependency chains.

| ID | Requirement | P | Area | Depends on | Status |
|---|---|---|---|---|---|
| [REQ-0005](#req-0005) | Report only verified actions | P0 | ai | [REQ-0032](#req-0032) | Done |
| [REQ-0007](#req-0007) | Permissions and policy in code | P0 | ai | [REQ-0027](#req-0027) | Done |
| [REQ-0021](#req-0021) | Failure tests | P0 | ml, ai | [REQ-0007](#req-0007), [REQ-0012](frontend-backend.md#req-0012), [REQ-0026](#req-0026), [REQ-0027](#req-0027) | Done |
| [REQ-0025](#req-0025) | Observability | P1 | ai | — | Done |
| [REQ-0026](#req-0026) | Bounded retries and safe fallback | P1 | ai | [REQ-0005](#req-0005) | Done |
| [REQ-0027](#req-0027) | Authentication, isolation and retention | P0 | ai, data | — | Done |
| [REQ-0028](#req-0028) | Reproducible setup | P0 | all | [REQ-0015](data-ml.md#req-0015), [REQ-0019](data-ml.md#req-0019) | Done |
| [REQ-0029](#req-0029) | Explanations from sources and rules | P1 | ai | [REQ-0025](#req-0025) | Done |
| [REQ-0032](#req-0032) | Documented mock tools | P1 | ai | — | Done |
| [REQ-0047](#req-0047) | No personal data to the LLM | P0 | ai | [REQ-0027](#req-0027) | Done |
| [REQ-0048](#req-0048) | Decision order | P0 | ai, ml | [REQ-0016](data-ml.md#req-0016) | Done |
| [REQ-0049](#req-0049) | Country as configuration | P2 | ai | — | Done |
| [REQ-0056](#req-0056) | Explicit trade-offs | P0 | all | [REQ-0016](data-ml.md#req-0016), [REQ-0055](analytics.md#req-0055) | In progress |

<a id="req-0005"></a>
### REQ-0005 · Report only verified actions

The system tells the customer an action happened only after reading it back. A timeout or an error is never reported as success.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 2 · Kickoff p. 11

**Depends on:** [REQ-0032](#req-0032). Read-back uses the tool contracts.

**Evidence:** Proven by: tool-failure tests where a failed or unconfirmed write produces a handoff, not a success message (`lookup_dispute` read-back and the `verify` record).

<a id="req-0007"></a>
### REQ-0007 · Permissions and policy in code

Who can see or do what is enforced by code in the service, not by instructions in the prompt, so a manipulated model still cannot break the rules.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 3; Data and execution boundaries · Kickoff p. 13

**Depends on:** [REQ-0027](#req-0027). Roles and per-customer checks need the session.

**Evidence:** Proven by: policy engine in code; roles enforced per route (customer routes need `customer`, `/api/v1/handoffs` needs `advisor`; a failure is a 403 recorded as `access_denied`); adversarial groups B, C and D in [`evidence/adversarial/20261001T130342Z/summary.json`](../../evidence/adversarial/20261001T130342Z/summary.json).

<a id="req-0021"></a>
### REQ-0021 · Failure tests

Test the cases the brief names explicitly: bad or missing data, expired session, unauthorized access, prompt injection, tool failure and multilingual ambiguity.

**Priority:** P0 · **Status:** Done · **Criterion:** Machine Learning · **Area:** ml, ai

**Source:** Problem statement: What your solution should demonstrate 5 · Kickoff p. 13

**Depends on:** [REQ-0007](#req-0007), [REQ-0012](frontend-backend.md#req-0012), [REQ-0026](#req-0026), [REQ-0027](#req-0027). The attacks test permissions, languages, fallback and the session.

**Evidence:** Proven by: 42 attacks in `tests/adversarial/` against the chat, the disputes API and the advisor endpoint, with `unsafe_outcome_rate` `0/42` (38 `blocked_verified`, 3 `passes_on_mock`, 1 `documented`, 0 `no_defense_yet`) in [`evidence/adversarial/20261002T222323Z/summary.json`](../../evidence/adversarial/20261002T222323Z/summary.json). A3 refuses prompt extraction in code, A4b records injection without changing the reply, and D4 bounds Gold reads (`SENTINEL_GOLD_TIMEOUT_S`, default 2 s, above the measured 0.28 s cold read). Runner fault injection (Gold, session, tool) degrades safely in [`evidence/evaluation-runs/2024Q4-eval-v6/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v6/summary.json).

<a id="req-0025"></a>
### REQ-0025 · Observability

Execution traces and logs for every turn, including country and language, so any conversation can be reconstructed.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15

**Evidence:** Proven by: per-step and turn records in `app/observability/` with country and language, replay by `trace_id` (`test_full_turn_is_replayable_by_trace_id`); the runner reads records by trace id in [`evidence/evaluation-runs/2024Q4-eval-v5/summary.json`](../../evidence/evaluation-runs/2024Q4-eval-v5/summary.json).

<a id="req-0026"></a>
### REQ-0026 · Bounded retries and safe fallback

Retries have a limit, failures fall back to a safe outcome (usually a handoff), and repeating an action never duplicates it.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15

**Depends on:** [REQ-0005](#req-0005). Retries are safe only when success is verified.

**Evidence:** Proven by: tool-failure tests, the `ModelUnavailable` fallback and idempotent dispute creation.

<a id="req-0027"></a>
### REQ-0027 · Authentication, isolation and retention

A trusted test session proves identity (a customer number alone does not), each customer reaches only their own records, and personal and conversation data has a retention policy.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering / Data Engineering · **Area:** ai, data

**Source:** Problem statement: What your solution should demonstrate 6; Data and execution boundaries · Kickoff p. 15

**Evidence:** Proven by: password login on `/api/v1/auth/*`; isolation matrix `test_foreign_access_attempts_are_blocked_8_of_8`; `me` returns role and country only; sessions and conversation stored by token hash and deleted on logout and expiry (`tests/test_state_sqlite.py`); the SQLite file, the turn log and the dev salt are created `0600` and a folder the app creates is `0700` (`test_database_file_is_owner_only`, `test_turn_log_and_dev_salt_are_owner_only`); startup fails if the state directory is not writable (`test_unwritable_state_path_fails_fast`) and `SENTINEL_SQLITE_JOURNAL=DELETE` opens the file in that mode (`test_journal_mode_delete`); the stored turn window is capped at 50; cookie, header, CSRF, rate-limit and input controls listed in [security](../build/security.md#controls-on-the-served-app-102-hardening); [retention table](../architecture/specification.md#data-retention). The deploy script keeps the file on an Azure Files share so a restart can keep an unexpired session; the public revision was redeployed with that share on 2026-10-03 and the cases survived a revision restart ([REQ-0035](delivery.md#req-0035)).

<a id="req-0028"></a>
### REQ-0028 · Reproducible setup

Anyone can set the project up, rerun the evaluation and get the same results, with versioned code and data runs.

**Priority:** P0 · **Status:** Done · **Criterion:** Rationale · **Area:** all

**Source:** Problem statement: What your solution should demonstrate 6 · Kickoff p. 15

**Depends on:** [REQ-0015](data-ml.md#req-0015), [REQ-0019](data-ml.md#req-0019). Reproducible pipeline and versioned runs.

**Evidence:** Proven by: stdlib evidence scripts with `verify` (`evidence/evaluation/eval_measure.py`, which also verifies against the pipeline DuckDB hash), write-once frozen runs, an offline replayable harness (`python3 -m eval.freeze`), and the data setup: sync the raw tables and run the pipeline in two steps ([`sentinel-data-engine/README.md`](../../sentinel-data-engine/README.md#9-local-development-quickstart)); a local run reproduced the committed quality report.

<a id="req-0029"></a>
### REQ-0029 · Explanations from sources and rules

Explanations cite data sources, policy rules and execution records. The model's hidden reasoning is not an audit artifact.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: What your solution should demonstrate 6

**Depends on:** [REQ-0025](#req-0025). Explanations cite the logged rules and sources.

**Evidence:** Proven by: `policy_rule` on every decide record and in the handoff evidence; the summary is built from turn codes, never from model reasoning (`tests/test_handoff_package.py`).

<a id="req-0032"></a>
### REQ-0032 · Documented mock tools

Mock banking tools are allowed if their contracts and limitations are documented.

**Priority:** P1 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Data and execution boundaries

**Evidence:** Proven by: tool and Gold contracts in the [specification](../architecture/specification.md#tool-contracts); mock and DuckDB Gold behind one seam with fallback (`tests/test_gold_duckdb.py`); memory and SQLite state behind the same ports; mocks listed in the [demo architecture](../architecture/demo-architecture.md#mocked-components).

<a id="req-0047"></a>
### REQ-0047 · No personal data to the LLM

The model never receives identifiers or personal data, and no restricted data goes into external model requests. Tools filter by the session customer instead.

**Priority:** P0 · **Status:** Done · **Criterion:** AI Engineering · **Area:** ai

**Source:** Problem statement: Data and execution boundaries · Own: [security](../build/security.md#llm-visibility)

**Depends on:** [REQ-0027](#req-0027). Tools filter by the session customer.

**Evidence:** Proven by: session-bound lookup that takes no customer argument plus the 8/8 denial test; auth events stored as salted `session_ref` records with no IP (`test_audit_session_ref_is_a_hash_not_the_customer`); router request whitelist that also keeps the fraud score out (`tests/test_ai_router.py`); the orchestrator sees an opaque customer hash, never the id; personal identifiers typed in free text are masked before the model (`app/privacy/`, `tests/privacy/`), so attack `A9` is `blocked_verified` in [`evidence/adversarial/20261002T120107Z/summary.json`](../../evidence/adversarial/20261002T120107Z/summary.json).

<a id="req-0048"></a>
### REQ-0048 · Decision order

When sources disagree, policy in code wins over the learned component, which wins over the LLM.

**Priority:** P0 · **Status:** Done · **Criterion:** Rationale / ML · **Area:** ai, ml

**Source:** Problem statement: introduction · Kickoff p. 11 · Own: [system](../architecture/specification.md#decision-priority)

**Depends on:** [REQ-0016](data-ml.md#req-0016). The order needs a learned component in between.

**Evidence:** Proven by: the [decision priority](../architecture/specification.md#decision-priority) in the specification.

<a id="req-0049"></a>
### REQ-0049 · Country as configuration

Country rules live in configuration files, so adding a country does not require new code.

**Priority:** P2 · **Status:** Done · **Criterion:** Rationale · **Area:** ai

**Source:** Own: [AI](../build/areas/ai.md#technical-rules)

**Evidence:** Proven by: per-country policy files in `sentinel-ai-core/config/policy/`.

<a id="req-0056"></a>
### REQ-0056 · Explicit trade-offs

Explain the trade-offs between autonomy, accuracy, latency, cost and human oversight, and justify where AI is used and where deterministic logic is better.

**Priority:** P0 · **Status:** In progress · **Criterion:** Rationale · **Area:** all

**Source:** Problem statement: introduction · Kickoff p. 11

**Depends on:** [REQ-0016](data-ml.md#req-0016), [REQ-0055](analytics.md#req-0055). Trade-offs are argued with the measured metrics.

**Evidence:** Proven by: the [decisions](../build/decisions/).

Missing: the argument with the final metrics, in the presentation.
