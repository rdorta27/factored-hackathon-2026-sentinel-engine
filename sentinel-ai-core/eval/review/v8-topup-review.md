---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# v8 top-up review (eval-v8 task 2.7)

Date: 2026-10-05.
Role: isolated reviewer.
This file records verdicts only. It proposes no new texts.

## Files read

- `eval/review/v8-topup-draft.jsonl` (96 rows, 24 bases `v8t-01` to `v8t-24`)
- `eval/review/v8-topup-provenance.md`
- `eval/cases/sealed_v8/intent.jsonl`
- `eval/cases/sealed_v8/multiturn.jsonl`
- `eval/cases/sealed_v8/attacks.jsonl`
- `eval/cases/sealed_v8/noisy.jsonl`
- `eval/cases.py`

The reviewer read no other files. The reviewer made no network calls.

## Check 1 — label check

Result: 1 wrong base (`v8t-13`, 4 rows). All other rows pass.

- Every row uses an intent from `INTENTS`. Every row uses split `held_out`.
- No row sets `expected_subtype`. An absent subtype is valid.
- `expected_slots` appears only on `v8t-22` and `v8t-23`. Keys stay in `SLOT_KEYS`. Amounts are non-negative numbers. Each slot value matches its own text.
- Variant, locale and country agree with `VARIANTS` on every row.
- Wrong rows: `v8t-13-es-MX`, `v8t-13-es-CO`, `v8t-13-es-AR`, `v8t-13-pt-BR`.
- Reason: the text asks for the account balance. The sealed set labels the same request `out_of_scope` with subtype `balance` (`v8i-38`). The draft labels it `status`. The label is wrong.

## Check 2 — near-copy check against sealed v8

Method: the reviewer compared each top-up `es-MX` text with every sealed v8 customer text. The reviewer used exact reading plus `SequenceMatcher` ratios as support.

Result: 1 base must drop.

| Top-up base | Closest sealed base | Ratio | Verdict |
|---|---|---|---|
| `v8t-13` | `v8i-38` (`¿Cuál es el saldo de mi cuenta?`) | 0.78 | DROP: same request, trivial rewording |
| `v8t-04` | `v8i-39` (personal loan) | 0.71 | KEEP: different ask (requirements vs request) |
| `v8t-12` | `v8i-49` (failed self-service) | 0.68 | KEEP: different channel (chat vs menu) |
| `v8t-18` | `v8i-35` (charge status) | 0.61 | KEEP: different ask (update timing, no merchant) |
| `v8t-23` | `v8i-08` (charge dispute) | 0.60 | KEEP: different merchant, amount, date, plus second request |
| `v8t-08` | `v8i-46` (pass to a person) | 0.57 | KEEP: adds a substantive wait-time clause |
| `v8t-15` | `v8i-36` (charge status) | 0.56 | KEEP: different object (case vs charge) |
| `v8t-03` | `v8i-40` (new card) | 0.55 | KEEP: adds an expiry reason |
| `v8t-22` | sealed attacks (best match) | 0.56 | KEEP: mixed-language form, own merchant and amount |
| All other bases | — | <= 0.54 | KEEP: distinct request or distinct wording |

Drop count for evidence: 1 base (4 rows).

## Check 3 — back-translation

Result: no drifters.

- `es-CO` and `es-AR` rows keep the `es-MX` meaning. Differences are locale wording only (`oficina`/`sucursal`, `crédito`/`préstamo`, voseo, `acá`/`aquí`).
- `v8t-05` uses one transfer rail per country (`SPEI`, `PSE`, `CBU`). The request stays the same.
- `pt-BR` rows translate the same request. Currency words follow the locale (`reais`/`pesos`).
- `v8t-22` and `v8t-23` use one amount per country (for example 850 / 850000 / 85000). This follows the sealed precedent (`v8m-01`: 1000 / 250000 / 45000). Each `expected_slots` value matches its own text. This is locale magnitude adaptation, not drift.
- Drifters: none.

## Check 4 — flavor bases

Result: all 6 flavor bases genuinely show their flavor. No drops.

| Base | Flavor | Verdict |
|---|---|---|
| `v8t-19` (`charge`) | Ambiguous | PASS: vague anomaly report, no explicit dispute words |
| `v8t-20` (`missing`) | Ambiguous | PASS: vague loss report, no charge details |
| `v8t-21` (`status`) | Mixed-language | PASS: Portuguese lead with a Spanish question in one turn on every variant |
| `v8t-22` (`charge`) | Mixed-language | PASS: Portuguese and Spanish mix in one turn, slots named |
| `v8t-23` (`charge` first) | Dual-intent | PASS: real second request with secondary `status` (`¿en qué va mi otro caso?`) |
| `v8t-24` (`status` first) | Dual-intent | PASS: real second request with secondary `charge` (`revisamos ese cobro que no reconozco`) |

## Drop list

Count: 1 base, 4 rows.

- `v8t-13-es-MX`, `v8t-13-es-CO`, `v8t-13-es-AR`, `v8t-13-pt-BR`
- Reasons: wrong intent (`status` for a balance inquiry; sealed `v8i-38` is `out_of_scope` with subtype `balance`); near-copy of sealed base `v8i-38` (same request, trivial rewording, ratio 0.78).

The reviewer recommends no other drops. The reviewer proposes no new texts.

## Post-drop base counts per intent

| Intent | Bases kept |
|---|---|
| `out_of_scope` | 6 (`v8t-01` to `v8t-06`) |
| `person` | 6 (`v8t-07` to `v8t-12`) |
| `status` | 7 (`v8t-14`, `v8t-15`, `v8t-16`, `v8t-17`, `v8t-18`, `v8t-21`, `v8t-24`) |
| `charge` | 3 (`v8t-19`, `v8t-22`, `v8t-23`) |
| `missing` | 1 (`v8t-20`) |
| Total | 23 bases, 92 rows |

## Completeness confirmation

Every remaining base holds exactly 4 variants: `es-MX`, `es-CO`, `es-AR`, `pt-BR`.
The remaining set is 4-variant complete: yes.
