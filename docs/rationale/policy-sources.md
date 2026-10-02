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
- **The window was written twice.** The customer texts repeated "90 días" while the value is `window_days`. *Fixed 2026-10-02:* the texts no longer carry a number; `tests/test_policy_texts.py` fails if one does. *Implemented 2026-10-02:* the follow-up "why?" answer reads the number from `window_days` and the dates from the verified charge, and states the demonstration label when `synthetic: true` (`explanation.window.expired`; `tests/test_explanation.py`). The rest of the Explain capability stays in the [chat plan](../../team/chat-behavior-plan.md).
- **One window for three countries,** although the sources read on 2026-10-02 differ: Argentina counts 30 days from receiving the statement, and no fixed window was found for Colombia (see the [verification table](#verification-table)). The value stays 90 as a declared demonstration policy ([021](../build/decisions/021-dispute-policy-sources.md)).
- **The engine cannot express what the sources say.** It counts days from the transaction date only, and it has no bank obligation (provisional credit, response time). The 5-day estimated time matches no source. Recorded in [021](../build/decisions/021-dispute-policy-sources.md#consequences); not built.
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

Filled on 2026-10-02 from a web search and page reads, not from a lawyer's review. **No value is loaded into a country file from this table until a person fills "Verified by".** One row per datum and source.

**Status** says how far each row is backed:

- `read in official source`: the official page or text was opened and the value read there.
- `secondary source only`: the value appears in news or search results, or in an official page that did not state it when read. It is not a citation.
- `not found`: no value was found. The cell is left empty on purpose, and no figure is estimated.

**Binds** says who the rule obliges: the bank toward the customer, or one bank toward another (card networks). A network time limit is not the customer's window.

| Country or network | Datum | Value | Binds | Norm | Link | Read on | Status | Verified by |
|---|---|---|---|---|---|---|---|---|
| MX | customer dispute window | 90 calendar days from the statement cut-off date or, where it applies, from the charge date | bank to customer | not cited by the page read | [CONDUSEF](https://www.gob.mx/condusef/es/articulos/cargos-no-reconocidos?idiom=es%2F1000) | 2026-10-02 | secondary source only: the official page read did not state the 90 days | |
| MX | provisional credit | the bank credits the amount about 48 hours after the claim | bank to customer | not cited by the page read | same | 2026-10-02 | read in official source | |
| MX | bank response time | investigation of up to 45 days; with no ruling after 45 days the claim is upheld | bank to customer | not cited by the page read | same | 2026-10-02 | read in official source | |
| CO | customer dispute window | | bank to customer | | [SFC FAQ](https://www.superfinanciera.gov.co/preguntas-frecuentes/14/14-tarjetas-debito-y-credito-fraudes-informaticos/) states none | 2026-10-02 | not found | |
| CO | bank response time | | bank to customer | | same | 2026-10-02 | not found. The "15 business days" seen in search results is the step before a complaint to the regulator, not a dispute window | |
| AR | customer dispute window (credit card) | 30 days from receiving the statement | bank to customer | Ley 25.065, art. 26 | [argentina.gob.ar](https://www.argentina.gob.ar/normativa/nacional/ley-25065-55556/actualizacion) | 2026-10-02 | read in official source | |
| AR | bank response time (credit card) | acknowledge within 7 days; correct or explain within 15 days (60 for foreign transactions) | bank to customer | Ley 25.065, arts. 26 to 27; the two reads disagreed on the article numbers and one result said 10 business days | same | 2026-10-02 | read in official source, article numbers to re-read | |
| AR | during the claim | the issuer cannot block the card for the amounts not contested | bank to customer | Ley 25.065, art. 28 | same | 2026-10-02 | read in official source | |
| AR | debit card | | bank to customer | | | | not found; not searched in the central bank's own rules | |
| Visa | issuer dispute time limit | 120 calendar days from the transaction, with exceptions by reason | bank to bank | Visa dispute rules | [Visa guidelines](https://usa.visa.com/dam/VCOM/global/support-legal/documents/merchants-dispute-management-guidelines.pdf) (PDF not readable by the tool) | 2026-10-02 | secondary source only | |
| Mastercard | issuer chargeback time frame | 120 days in some cases; 90 days from the settlement date for "all other" transactions, per a search result | bank to bank | Mastercard Chargeback Guide | [Mastercard guide](https://www.mastercard.com/content/dam/public/mastercardcom/na/global-site/documents/chargeback-guide.pdf) | 2026-10-02 | secondary source only: the search result and Visa's figure differ, and the guide was not opened | |

Read this table with three limits:

- The rows describe card claims. No row covers debit versus credit in every country, and Argentina's debit card rules were not searched.
- No card network field was found in the code, configuration or pipeline; the official data dictionary was not checked. Until it is, a network limit is a cited source and is not applied per card.
- The country sources count the window from different dates (statement cut-off, statement receipt, charge). The engine counts from the transaction date only.

## In production

A bank edits the YAML (`source`, `synthetic: false`) and the chat reads the window from
`window_days` instead of from a text: the "why?" answer carries the stored `window_days`,
the charge date and the last eligible date, and drops the demonstration label when
`synthetic` is false. Each decision already records the version of the country file. A
change of a value is recorded as a new decision that replaces 003.

## On the slide

"The policy is configuration, decided in code, and labelled as a demonstration policy
until a bank replaces it."
