# Design

## Context

See proposal.md for motivation. Current state that shapes the approach:

- `sentinel-ai-core/eval/` does not exist. The loop runs through `POST /chat`
  with a test session and the model behind one port (from
  `add-prompted-llm-router`).
- The structured log already recovers a turn by `trace_id` through
  `Recorder.records_for`, and the response carries `X-Trace-Id`.
- `tests/adversarial/conftest.py` already has reusable fault patterns:
  `RaisingGold`, `EmptyGold`, `expire_session`, and per-session `InMemoryTools`.
- The frozen label set and its provenance come from
  `add-evaluation-evidence` as `eval/labels.json`.

## Goals / Non-Goals

**Goals:**
- One harness that measures both the component (four pillars) and the system
  (outcome metrics) from the same case set.
- Reproducible offline runs and write-once frozen results.
- Honest reporting: n, case mix, versions, variability and failures.

**Non-Goals:**
- Implementing the router, the baseline or the label evidence.
- A dashboard, a release gate or an LLM judge.
- Real user data: cases are team-written and declared simulation.

## Decisions

### Decision: one spine, two drivers

A shared `Case` model and a `metrics.py` of pure functions over outcomes serve
two drivers: `bench_router.py` calls the model port directly over the intent
cases (component, four pillars), and `runner.py` replays full cases against
`POST /chat` and reads the logs (system). Both write through one `report.py` to
the same `summary.json` shape, so a reader compares the two levels without
relearning the format. Alternative: two separate harnesses (rejected: duplicated
case handling and report format).

### Decision: one JSONL case schema for both levels

Each case carries component labels (`expected_intent`, `expected_category`) and
system labels (`expected_outcome`, `requires_handoff`), plus locale, country,
turns, tags and split. The component driver uses the intent labels; the system
driver uses the outcome labels. One set keeps the two levels on the same cases.

### Decision: fault injection through app state, reusing the adversarial patterns

The system driver injects faults by overriding `app.state.gold` and the session
store, reusing `RaisingGold`, `EmptyGold` and `expire_session` from
`tests/adversarial/conftest.py` rather than editing the router. A case declares
its fault in a field, and the runner applies it before the replay.

### Decision: trace id is the join key

The runner reads `X-Trace-Id` from the response and recovers the turn records
with `records_for`. Metrics are computed from the recovered records and the
response body, never from a second instrumentation.

### Decision: stability as repeated agreement

Stability repeats a case N times and reports the agreement (the share of runs
matching the modal outcome). The same repetition feeds latency and cost
variability. N is configuration, small by default to bound cost.

### Decision: honest cost assumptions

Cost comes from the recorded token and cost fields; the per-resolution figure
uses the documented assumptions and is labelled as a projection. When there are
no resolutions the metric is "not defined", never zero.

### Decision: offline through fixtures

The harness runs with the `FixtureTransport` from the router change, so a run
opens no connection and a re-run reproduces the same summary.

### Decision: write-once results under `evidence/evaluation-runs/`

A run writes `summary.json` and `report.md` to a new run-id folder and refuses to
overwrite an existing one, matching the evidence convention. The dataset
evidence stays in `evidence/evaluation/`; the two producers are kept apart.

## Risks / Trade-offs

- [Synthetic set too small to be meaningful] → report n and the small-sample
  limits per locale and class, and keep the mix proportional to the real one.
- [Stability multiplies cost] → N is configuration and the fixture transport is
  free; the live model is used only when configured.
- [Fault injection couples the runner to internals] → it reuses the adversarial
  fixtures and never edits the router.
- [Cost assumptions unknown] → report measured tokens and cost, and label the
  ROI as a projection with its assumptions stated.
- [A result without its label provenance] → the summary records the label set run
  id and hash.

## Migration Plan

Additive. The harness is a separate entry point; nothing in the service changes.
Rollback is removing `eval/` and the run folders.

## Open Questions

- How many cases per locale and class (pending, tied to who authors them).
- The default N for the stability runs.
