# Tasks

Paths under `ai-core/` mean `sentinel-ai-core/`. Run tests from `sentinel-ai-core/` with `python -m pytest -q`.

## 1. Rules before results

- [x] 1.1 Amend `docs/build/decisions/016-router-models.md` with D1 to D3 (design §1): the pt-BR condition as a paired net loss of at most 3 per 30 development bases, the route-rule candidates, and "every turn to strong" as the fallback; status of the amendment is Proposed. Verify: the commit date predates any `2024Q4-select-*` run (`git log --format=%cI -- docs/build/decisions/016-router-models.md`). Area: `docs/build/areas/ml.md`.
- [x] 1.2 Write `docs/build/decisions/018-evaluation-acceptance.md` from `_template.md` with D4 to D7, their thresholds and the sizing basis (design §1 and §2), status Proposed. Verify: the file exists, cites 016 and 017, and is committed before any held-out run. Area: `docs/build/areas/ml.md`.
- [x] 1.3 List the change in `docs/requirements/requirements.md` against REQ-0012, 0013, 0016, 0017, 0020, 0022 and 0024, and cite 018. Verify: each row links the decision. Area: `docs/build/areas/analysis.md`.

## 2. Model port: recordings, price, bounded output

- [x] 2.1 Key recordings by model, prompt version, input and repetition, and store those four in clear text in each file. Keep `FixtureTransport` serving the old `v1-<hash>.json`. Verify: new tests in `ai-core/tests/test_ai_router.py` show two models and two repetitions get distinct recordings, and the existing suite passes unchanged. Spec: llm-router "Offline replay is deterministic".
- [x] 2.2 Add the dated price table (from 016) and compute `cost_usd` per serving model; refuse an unpriced model in recording mode. Verify: a test prices the same tokens differently for a cheap and a strong model, and a test sees the refusal. Spec: llm-router "Cost uses the model's own price".
- [x] 2.3 Send `response_format` JSON, a `max_tokens` cap and the lowest reasoning setting; count an invalid reply as a JSON failure. Verify: a test with a fake HTTP server asserts the request body and the failure count. Spec: llm-router "Output is bounded JSON".
- [x] 2.4 Add `RecordingTransport`: serve on a hit, call live on a miss only in recording mode, and refuse to write content that contains the API key or an authorization header. Verify: tests show a hit makes no call, a miss outside recording mode raises, and a planted key blocks the write. Spec: llm-router "Live responses are recorded once".
- [x] 2.5 Add prompt version `v2` with a fixed example block built only from development ids, and record those ids with the version. Verify: a test fails when a held-out id is passed as an example. Spec: llm-router "A prompt version with development examples".
- [x] 2.6 Document recording in `ai-core/README.md`: `.env` from `.env.example`, `chmod 600`, `git check-ignore -v .env`, `set -a; source .env; set +a`, a provider spend limit of USD 1, and a pre-commit grep of staged recordings for `Authorization`, `Bearer` and the key prefix. Verify: a teammate can follow it as written with `SENTINEL_LLM_BASE_URL` empty, and the suite still runs offline. Decision: 016.

## 3. Case schema and sealing tools

- [x] 3.1 Add `base_id`, `variant`, `perturbation` and the `noisy` tag to `ai-core/eval/cases.py`, and reject a variant that contradicts locale or country. Verify: `ai-core/tests/test_eval_cases.py` covers the contradiction and the noisy reference. Spec: evaluation-runner "Versioned labelled case set".
- [x] 3.2 Move the 10 earlier held-out cases into development. Verify: `held_out.jsonl` is removed or empty, `check_splits` passes, and a test asserts no earlier held-out id is in `eval/cases/sealed/`. Spec: sealed-case-set "Earlier held-out cases are retired".
- [x] 3.3 Add a seal command that checks sizes (at least 70 bases, at least 25 per intent, 4 variants per base) and writes `ai-core/eval/cases/seal.json` with hash, counts, date and author. Add the append-only `ai-core/eval/measured.json`. Verify: tests show an undersized set is refused and an edited sealed file fails the hash check. Spec: sealed-case-set "Held-out set is sealed before measuring".

## 4. Development cases (written by the prompt author)

- [ ] 4.1 Write 30 development bases in es-MX, spread across intents and with ambiguous wording. Verify: the cases load and the intent counts show in `case_mix`. Glossary: `docs/understand/glossary/`.
- [ ] 4.2 Generate the es-CO, es-AR and pt-BR variants with one model and back-translate them with another, then record the review per case and fix or drop any drift. Verify: 120 development cases load, and each non-team variant has a review record. Decision: 017.

## 5. Held-out cases (written by someone other than the prompt author)

- [ ] 5.1 Write held-out bases 1 to 35 in es-MX. Verify: they load under `eval/cases/sealed/`. Decision: 017.
- [ ] 5.2 Write held-out bases 36 to 70 in es-MX. Verify: 70 bases load and every intent has at least 7 bases.
- [ ] 5.3 Generate and back-translate the three other variants for all 70 bases. Verify: 280 cases load.
- [ ] 5.4 Review back-translations for bases 1 to 35, fixing or dropping drift. Verify: each case has a review record.
- [ ] 5.5 Review back-translations for bases 36 to 70. Verify: each case has a review record.
- [ ] 5.6 Write 50 noisy twins of held-out cases, one declared perturbation each. Verify: each names its base, variant and perturbation, and the loader accepts them.
- [ ] 5.7 Write 75 attacks, including pt-BR injection, from the patterns in `ai-core/tests/adversarial/`, and mark the code-decided ones. Verify: the loader accepts them and the count is 75.
- [ ] 5.8 Seal the held-out, noisy and attack files. Verify: `seal.json` is committed and its commit predates task 8.2. If 70 bases are not ready by 2026-10-03 18:00 UTC-5, stop and amend this change to 50 bases first (design, Risks).

## 6. Runner metrics and guards

- [ ] 6.1 Report per-variant and per-intent metrics with n and a 95% base-level bootstrap interval, and label breakdowns wider than ±10 points as descriptive. Verify: tests in `ai-core/tests/test_eval_metrics.py` with a fixed seed. Spec: evaluation-runner "Every result carries n, mix, versions and variability".
- [ ] 6.2 Add the paired comparison (fixed and broken ids, net difference and interval) and the per-variant net loss in shared bases. Verify: a hand-built example gives the expected lists and counts. Spec: evaluation-runner "Paired comparison with intervals".
- [ ] 6.3 Run three versions (baseline, `v1`, `v2`) in the bench on identical ids, and compute stability from recorded repetitions only. Verify: a test proves identical ids, and a single-recording case is left out of the stability n. Spec: evaluation-runner "Stability comes from recorded repetitions".
- [ ] 6.4 Add the spend cap (default 0.45) and refuse to freeze a capped run. Verify: a test with a fake priced transport stops at the cap and writes no summary. Spec: evaluation-runner "Spend cap".
- [ ] 6.5 Split the freeze into `select` (development only, fails on a held-out case) and `measure` (checks the seal hash and `measured.json`, then appends). Verify: tests for both refusals. Spec: evaluation-runner "Selection runs on development only" and "Baseline and system on the same held-out set".
- [ ] 6.6 Show variant, paired and stability sections in `ai-core/eval/report.py`, rendered from `summary.json` fields only. Verify: the `test_eval_report.py` snapshot includes them.

## 7. Model selection (development, live, about USD 0.09)

- [ ] 7.1 Run the token probe: 10 development cases × 3 candidates, recorded. Verify: each model id from 016 resolves (correct the DeepSeek id in 016 if the other form is the valid one), recordings show real and cached tokens; if output exceeds 200 tokens, adjust the cap and re-estimate the budget in design §6 before going on. Decision: 016.
- [ ] 7.2 Run `select` over 120 development cases for the candidates and freeze `evidence/evaluation-runs/2024Q4-select-v1/`. Verify: `summary.json` holds JSON-failure counts, accuracy per route and the pt-BR paired loss for each candidate.
- [ ] 7.3 Accept D1 to D3 in 016, citing `2024Q4-select-v1` fields, and set the chosen model ids in your local `.env` only. Verify: the decision cites field paths, and `git status` shows no `.env`.

## 8. Held-out measurement (once, live, about USD 0.26)

- [ ] 8.1 Record `v1` and `v2` on the sealed set, with 3 repetitions of `v2` on 25 bases. Verify: the spend stays under the cap, and the staged recordings pass the secret grep from 2.6.
- [ ] 8.2 Run `measure` and freeze `evidence/evaluation-runs/2024Q4-eval-v7/`. Verify: `measured.json` gains the seal hash, and a second `measure` is refused.
- [ ] 8.3 Accept or reject D4 to D7 in 018, citing `2024Q4-eval-v7` fields, including the failures and the per-variant losses. Verify: every number in 018 is a cited field path.
- [ ] 8.4 Update the REQ-0016, 0017, 0020, 0022 and 0024 status rows, and the limits note for REQ-0013 (no native-speaker review, no strict equivalence between variants). Verify: the rows link `2024Q4-eval-v7`.

## 9. Integration check

- [ ] 9.1 With no network and `SENTINEL_LLM_BASE_URL` empty, run the full suite and replay `2024Q4-eval-v7` offline. Verify: tests pass and the replayed summary matches the frozen one.
- [ ] 9.2 Run `openspec validate llm-evaluation --strict` and grep the branch diff for the key prefix, `Authorization` and `Bearer`. Verify: validation passes and the grep is empty.
