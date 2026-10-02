# Policy sources

The dispute policy the chat applies is synthetic. This page lists what is
synthetic, what a customer can see of it, the known defects, and where real values
could come from. The policy is decided in code ([REQ-0033](../requirements/frontend-backend.md#req-0033)),
never by the model. Thresholds are covered in [policy thresholds](policy-thresholds.md);
this page is the whole inventory.

## Choice

The policy lives in `sentinel-ai-core/config/policy/{mx,co,ar}.yaml`, marked
`synthetic: true` ("Synthetic policy written by the team. Not a bank policy"). A bank
replaces the values, points `source` at its own policy and sets `synthetic: false`,
with no code change. Until then the chat must not present the values as a bank's rules.

## What is synthetic and what the customer sees

| What the customer sees | Where it lives | Origin | State |
|---|---|---|---|
| "Outside the 90-day window" | `window_days: 90` in the three country files | team assumption, source unconfirmed ([003](../build/decisions/003-disputes-flow.md)); the team's own Gold view filters on the same 90 days ([sizing](../sizing_capacity.md#22-eligible-dispute-volume-90-day-window)), so it agrees with the policy but is not an independent source | same value for all three countries |
| "Because of the amount, an advisor will review" | `thresholds.high_amount` per currency | p95 of 2024Q4 charges ([011](../build/decisions/011-high-amount-threshold.md)) | a workload choice, not a business rule; MXN has no value |
| A handoff on suspected fraud | `thresholds.fraud_score` and the "not me" wording ([010](../build/decisions/010-fraud-handoff-rule.md)) | p95 of 2024Q4 scores | the customer never sees the word fraud |
| Which statuses can be disputed | `statuses:` in the country files | team decision | pending, reversed and declined are not disputable |
| "Estimated time (demonstration value)" on a handoff | `_sla_date` in `app/routers/demo_chat.py`: reference date plus 5 calendar days | invented | labelled as a demonstration value |
| "Today" | `demo_today` and `SENTINEL_REFERENCE_DATE`, 2026-06-17 | fixed demo date over 2024Q4 data | stated in the health route |

## Known defects

- **An invented citation** ("within the 90-day window (Art. 4)", `ruleEligible`). No such article exists in the repository. *Fixed 2026-10-02:* removed from es-419 and pt-BR.
- **The window was written twice.** The customer texts repeated "90 días" while the value is `window_days`. *Fixed 2026-10-02:* the texts no longer carry a number; `tests/test_policy_texts.py` fails if one does. The number comes back, read from `window_days`, with the follow-up "why?" answer in the [chat plan](../../team/chat-behavior-plan.md).
- **One window for three countries,** although real windows differ by country and product. Open until the verification table is filled.
- **The estimated time** was a demo value presented without a label. *Fixed 2026-10-02:* the field reads "estimated time (demonstration value)" in es-419 and pt-BR. The 5-day value itself is still invented.

## Where real values could come from

In order of weight:

1. **The bank's own policy:** dispute windows, amounts that need a person, response times. What actually applies.
2. **The regulator of each country:** minimum time for the customer to dispute a charge and maximum time for the bank to answer. México: CNBV, Banxico, CONDUSEF. Colombia: Superintendencia Financiera. Argentina: BCRA. For pt-BR customers, Brazil: Banco Central and the consumer-defence code.
3. **Card network rules** (Visa, Mastercard): chargeback time limits between banks.

Real windows probably differ by country, by product (debit or credit) and by the
starting point (transaction date or statement cut-off date). No figure is entered from
memory: every value below is filled only from the official text.

## Verification table

Empty until someone reads the official source. One row per datum and country.

| Country | Datum | Value | Norm | Link | Read on | Verified by |
|---|---|---|---|---|---|---|
| MX | customer dispute window | | | | | |
| MX | bank response time | | | | | |
| CO | customer dispute window | | | | | |
| CO | bank response time | | | | | |
| AR | customer dispute window | | | | | |
| AR | bank response time | | | | | |

## In production

A bank edits the YAML (`source`, `synthetic: false`) and the chat reads the window from
`window_days` instead of from a text. Each decision already records the version of the
country file. A change of a value is recorded as a new decision that replaces 003.

## On the slide

"The policy is configuration, decided in code, and labelled as a demonstration policy
until a bank replaces it."
