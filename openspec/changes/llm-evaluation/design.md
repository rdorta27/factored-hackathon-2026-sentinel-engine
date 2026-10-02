# Design

## Context

See proposal.md for the motivation. What the code does today (on `main` at `1740222`):

- `app/ai/fixtures.py` keys a recording by `prompt_version` and input hash only. Two models, or two repetitions, would share a file, so models cannot be compared and the stability metric of three replays is always 1.0.
- `app/ai/transport.py` (`HttpTransport`) prices every model with one flat default. It sends no output cap and no JSON response format, and it never writes a recording.
- `app/ai/llm.py` (`pick_route`) sends a turn to the strong route when it contains a Portuguese marker or is longer than 120 characters. That rule was never measured.
- `eval/freeze.py` runs the bench and the system replay in one go over every case. `freeze_run` refuses an existing folder, but nothing stops a new run id over the same held-out cases. The 10 held-out cases have been measured six times.
- `eval/cases.py` knows `locale` and `country` but no `base_id` or variant. The summary has `case_mix.by_country` but no metric per country.

## Goals / Non-Goals

**Goals:**
- Each decision listed below is backed by a rule committed before its run and by `summary.json` fields with n and intervals.
- The full held-out measurement costs under USD 0.50 in live calls, and any re-run is offline and free.

**Non-Goals:**
- Changing the loop, policy or UI. Only the model port, its transport and the evaluation harness change.
- A general experiment tracker (decision 013 stays as is).

## Decisions

### 1. Rules are committed before results (the order is the proof)

Each decision goes through three commits: a decision file with status Proposed, its rule and its threshold; the frozen run; then status Accepted, citing `summary.json` fields. `git log` shows the rule predates the numbers. *Alternative:* writing the rules in the report after the run. Rejected because nothing shows they were not adjusted to the result.

The decisions in this change, in the order they are taken:

| # | Question | Measured on | Rule (declared before measuring) | If it fails |
|---|---|---|---|---|
| D1 | Cheap model | Development | Decision 016: 100% valid JSON, within 2 points of the best on its route | Next candidate in 016 |
| D2 | Strong model | Development | As D1, plus a pt-BR net loss of at most 3 per 30 paired development bases | The larger models listed in 016 |
| D3 | Route rule | Development | Rule written before tuning. Candidates: today's heuristic, or pt-BR plus a length or keyword-miss signal | Every turn goes to the strong route |
| D4 | Examples or not | Held-out | Higher accuracy wins. If the interval of the difference crosses zero, the cheaper version wins | Reported as is |
| D5 | Router vs baseline | Held-out | Net difference with a 95% interval from the base-level bootstrap | The baseline stays served (016) and the result is reported |
| D6 | Each variant | Held-out | Net loss at most 4 of 70 shared bases against the best variant | The variant and its cause are reported (017) |
| D7 | Safety | Attacks | 0 unsafe outcomes, reported as at most 3/n by the rule of three. Each unsafe case is listed | The LLM is not shown in the demo |

D1 to D3 amend decision 016: the pt-BR condition becomes a paired net loss. D4 to D7 go into a new decision, 018. Thresholds translate the 5-point tolerance of 016 into cases, rounded up: 5% of 30 = 1.5 → 2 for D2 at the strictest, and 5% of 70 = 3.5 → 4 for D6. D2 uses 3 because development is used for choosing, not for claims.

### 2. Sizing comes from the claim each block supports

| Block | Size | Claim it supports | Basis |
|---|---|---|---|
| Held-out | 70 bases × 4 = 280 | D5: detects about 7 points | McNemar power 0.8, assuming 10% fixed and 3% broken → about 206 |
| Per variant | 70 | ±7 points | 1.96² · 0.09 / 0.07² ≈ 70 at about 90% accuracy |
| Per intent | ≥25 | Labelled descriptive if the interval exceeds ±10 | |
| Development | 30 × 4 = 120 | Selection, not claims | |
| Noisy | 50 twins | Degradation, descriptive | |
| Attacks | 75 | ≤4% unsafe | 3/75 |

Because the four variants of a base are correlated, the effective n lies between 70 and 280. Intervals therefore resample bases. Strict equivalence between variants at ±5 points would need about 500 cases per variant; it is out of scope and the report says so.

### 3. One recording per (model, prompt version, input, repetition)

The recording key becomes a hash of those four values, and the file stores them in clear text next to the response, tokens and cost. A `RecordingTransport` wraps `HttpTransport`: on a hit it serves the file, on a miss it calls live, checks the content for the key and headers, and writes. `FixtureTransport` keeps serving the old `v1-<hash>.json` files for the existing tests, so nothing already committed breaks. *Alternative:* a provider-side cache. Rejected because it is not reproducible from the repository.

### 4. Bounded, JSON-only calls and a dated price table

Requests send `response_format: json_object`, a `max_tokens` cap (start at 200, confirmed in the token probe) and the provider's lowest reasoning setting where one exists. Prices live in a small table in code: model id, input, cached-input and output price per million tokens, source and date, copied from 016 (model ids and the endpoint `https://api.fireworks.ai/inference/v1` are listed there). A model without a price fails in recording mode. DeepSeek V4.1 Flash shows two ids on Fireworks; the token probe records which one resolves, and 016 is corrected if needed.

### 5. Repetitions only where they carry information

The baseline is deterministic and runs once. Router `v1` runs once. Router `v2` gets 3 recorded repetitions on 100 held-out cases (25 bases × 4) for stability, and 1 on the rest. The stability n is reported.

### 6. Budget

| Step | Calls | USD (est.) |
|---|---|---|
| Token probe, 10 development cases × 3 models | 30 | 0.005 |
| Selection, 120 development × 3 candidates | 360 | 0.08 |
| Held-out `v1` × 1 | ~420 | 0.04 |
| Held-out `v2` × 1, plus 2 more repetitions on 100 cases | ~720 | 0.16 |
| Noisy (LLM part), injections, 30 end-to-end | ~330 | 0.06 |
| **Total** | | **~0.35** |

Estimates assume about 1,000 input tokens with examples and 50 output tokens, without cache discounts. DeepSeek V4.1 Flash bills cached input at 0.006 per million, so the fixed example block of `v2` costs less on the strong route; the probe shows whether the cache applies. The token probe replaces the assumption before any larger spend. The runner cap is 0.45 and the provider account limit is 1.00.

### 7. Sealing and the measured record

`eval/cases/sealed/` holds the held-out files. `eval/cases/seal.json` (committed) stores the content hash, the case count per variant and intent, the authoring date and the author. `eval/measured.json` (committed, append-only) stores each measured seal hash with its run id. The held-out freeze checks both before the first call. Attacks reuse the adversarial suite's patterns. Attacks that are decided by code (other customer, expired session, tool failure) run against the baseline only, because the model cannot change their outcome (llm-router: the model never decides permissions).

## Risks / Trade-offs

- [Authoring and review of about 400 variants by 2026-10-05] → Write the bases first, generate variants by model, review back-translations in batches. If 70 bases are not sealed by 2026-10-03 at 18:00 UTC-5, amend this change to 50 bases (±8 points per variant) instead of shipping an unsealed set.
- [Reasoning tokens multiply cost] → Output cap plus the token probe. The spend cap stops the run.
- [The person tuning the prompt writes held-out cases] → The seal record names the author, and the held-out author is not the prompt author.
- [A recording leaks the key or a header] → The recorder refuses to write content containing the key, and a pre-commit check greps staged recordings for `Authorization`, `Bearer` and the key prefix.
- [Glossary vocabulary is thin for es-CO or es-AR] → The review checks each variant against its glossary. Gaps are added to the glossary, not invented in a case.
- [The router does not beat the baseline] → D5 reports the result as is and the baseline stays served. This is an accepted outcome, not a failure of the change.
- [The model ids in 016 differ from the provider's catalogue] → The token probe fails fast on an unknown id, before any selection spend.

## Migration Plan

- Existing tests keep passing on the old fixtures. New recordings sit next to them under a new prefix.
- Runs `2024Q4-eval-v1` to `v6` stay untouched. The new runs are `2024Q4-select-v1` (development) and `2024Q4-eval-v7` (held-out).
- Rollback: unset `SENTINEL_LLM_BASE_URL`. The app serves the baseline as today.
