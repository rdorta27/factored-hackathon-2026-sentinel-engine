# Demo review

pt-BR back-translation signed by a model other than the writer. Spanish country variants are not a second language: the baseline classifies all three as `es-419`. es-CO was checked by a Colombian teammate. es-MX and es-AR were checked by DeepSeek V4.1 Flash, not by a native speaker.

| Field | Value |
|---|---|
| Writer | grok-4.7 |
| Back-translator | fireworks-ai/accounts/fireworks/models/deepseek-v4p1-flash |
| Reviewer model | fireworks-ai/accounts/fireworks/models/deepseek-v4p1-flash |
| pt-BR signed | yes, 2026-10-02 |
| es-CO team check | yes, 2026-10-02, after the peso was named mexicano |
| es-MX / es-AR | signed by DeepSeek V4.1 Flash, 2026-10-02; no native speaker |

A row is OK only if meaning, amount, merchant and intent match. `não reconheço` is not `não fui eu`. `R$` is not the account currency.

The reviewer marked `probe-unrecognized` and `probe-brl-amount` as not OK because the intended Spanish omitted the date the Portuguese includes. The Portuguese was not changed. The intended Spanish below includes 12 de junio, which the back-translation already had. Those two are signed after that reference fix, not because the reviewer was asked again.

## pt-BR scripts

| OK | Case | Intended Spanish | pt-BR | Back-translation | Note |
|---|---|---|---|---|---|
| [x] | `demo-normal-pt-BR` | No reconozco un cargo de 320 en Cafe Central del 12 de junio. | não reconheço uma cobrança de 320 no Cafe Central em 12 de junho | No reconozco un cargo de 320 en Cafe Central del 12 de junio. | MXN, not BRL. Confirm box, then case number only after read-back. |
| [x] | `demo-ambiguous-pt-BR` | No reconozco un cargo. / No lo reconozco, ¿lo pueden revisar? | não reconheço uma cobrança / não reconheço, pode revisar? | No reconozco un cargo. / No lo reconozco, ¿pueden revisarlo? | Word order only. No merchant, no amount. Nothing opens. |
| [x] | `demo-human-pt-BR` | Quiero hablar con un asesor. | quero falar com um atendente | Quiero hablar con un asesor. | First offer, second handoff. |

## pt-BR probes

| OK | Case | Intended Spanish | pt-BR | Back-translation | Note |
|---|---|---|---|---|---|
| [x] | `probe-unrecognized` | No reconozco el cargo de 320 en Cafe Central del 12 de junio. | não reconheço uma cobrança de 320 no Cafe Central em 12 de junho | No reconozco un cargo de 320 en Cafe Central del 12 de junio. | Reference corrected to include the date. Not a fraud claim. |
| [x] | `probe-not-mine` | No fui yo, clonaron mi tarjeta. | não fui eu, clonaram meu cartão | No fui yo, clonaron mi tarjeta. | Handoff on `fraud.claim` after the customer selects the charge. |
| [x] | `probe-brl-amount` | No reconozco un cargo de R$ 320 en Cafe Central del 12 de junio. | não reconheço uma cobrança de R$ 320,00 no Cafe Central em 12 de junho | No reconozco un cargo de R$ 320,00 en Cafe Central del 12 de junio. | Reference corrected to include the date. `R$` kept. Must not open a case. |
| [x] | `probe-saldo` | ¿Cuál es mi saldo? | qual é o meu saldo | ¿Cuál es mi saldo? | Out of scope. Handoff. |

## Brazilian terms

Pix is matched as a word (`\bpix\b`), so a merchant such as pixelmart stays a charge. It is not in the sealed set. A Pix ask hands off: the account has no Pix. `extrato` and `fatura` are the statement and bill words inside sealed charge inquiries (`ho-b01-pt-BR`, `ho-b25-pt-BR` and others). Marking them out of scope would change that measurement, so a bare ask shows the account's charges instead of inventing a Brazilian statement.

| OK | Case | Intended Spanish | pt-BR | Back-translation | Served behavior |
|---|---|---|---|---|---|
| [x] | `probe-pix` | Quiero hacer un Pix. | quero fazer um pix | Quiero hacer un Pix. | handoff, out of scope |
| [x] | `probe-extrato` | Quiero ver el estado de cuenta. | quero ver o extrato | Quiero ver el estado de cuenta. | clarification with the account's charges |
| [x] | `probe-fatura` | Quiero ver la factura. | quero ver a fatura | Quiero ver la factura. | clarification with the account's charges |

## Spanish variants

Account stays with the charge. The variant is the wording. es-MX and es-AR were checked by DeepSeek V4.1 Flash, not by a speaker. es-CO was checked by a Colombian teammate. The first normal line was rejected; the rewrite below was accepted. The three glossaries use the same person phrase, so the human lines match on purpose.

| OK | Case | Line | Who checks |
|---|---|---|---|
| [x] | `demo-normal-es-CO` | No reconozco el cobro de 320 pesos mexicanos en Cafe Central, el día 12 de junio. | Team, es-CO, 2026-10-02. The first wording (320 pesos, no country) was rejected: it reads as Colombian. This rewrite was accepted. DeepSeek also found no drift in amount or merchant. |
| [x] | `demo-ambiguous-es-CO` | No reconozco un cobro. / ¿Lo pueden revisar? | Team, es-CO, 2026-10-02 |
| [x] | `demo-human-es-CO` | Quiero hablar con un asesor. | Team, es-CO, 2026-10-02 |
| [x] | `demo-normal-es-MX` | Vi en mi estado de cuenta un cargo de 320 pesos mexicanos de Cafe Central del 12 de junio y no lo reconozco. | DeepSeek V4.1 Flash, 2026-10-02. No drift. |
| [x] | `demo-ambiguous-es-MX` | No reconozco un cargo. / No lo reconozco, ¿lo pueden revisar? | DeepSeek V4.1 Flash, 2026-10-02. No drift. |
| [x] | `demo-human-es-MX` | Quiero hablar con un asesor. | DeepSeek V4.1 Flash, 2026-10-02. No drift. |
| [x] | `demo-normal-es-AR` | En el resumen me figura un cargo de 320 pesos mexicanos de Cafe Central del 12 de junio y no lo reconozco. | DeepSeek V4.1 Flash, 2026-10-02. No drift. No native speaker. |
| [x] | `demo-ambiguous-es-AR` | Me figura un cargo y no lo reconozco. / ¿Lo revisan? | DeepSeek V4.1 Flash, 2026-10-02. No drift. |
| [x] | `demo-human-es-AR` | Quiero hablar con un asesor. | DeepSeek V4.1 Flash, 2026-10-02. No drift. Not `representante`. |
