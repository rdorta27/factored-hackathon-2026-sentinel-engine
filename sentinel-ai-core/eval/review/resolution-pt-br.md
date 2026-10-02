# Resolution set — pt-BR review

Back-translation of the pt-BR variants of the resolution set, signed by a model
other than the writer, as in [017](../../../docs/build/decisions/017-portuguese.md).
The pt-BR cases are a Brazilian-language customer of an MX, CO or AR account, so
currency, policy and thresholds follow the account; only the wording is pt-BR.

| Field | Value |
|---|---|
| Writer | grok-4.7 |
| Back-translator | fireworks-ai/accounts/fireworks/models/deepseek-v4p1-flash |
| Reviewer model | fireworks-ai/accounts/fireworks/models/deepseek-v4p1-flash |
| pt-BR signed | yes, 2026-10-02 |

The resolution set uses two opening messages per language: a vague one (the
customer names no charge, then picks one) and, for the "not mine" situation, a
claim that the charge is not theirs. A row is OK only if meaning and intent
match; no amount, merchant or date is stated in either language.

| OK | Use | pt-BR | Back-translation |
|---|---|---|---|
| [x] | vague (1) | não reconheço uma cobrança | No reconozco un cargo. |
| [x] | vague (2) | tem um lançamento que não fiz | Hay un movimiento que no hice. |
| [x] | not mine (1) | não fui eu, alguém usou meu cartão | No fui yo, alguien usó mi tarjeta. |
| [x] | not mine (2) | não autorizei essa cobrança, clonaram meu cartão | No autoricé ese cargo, clonaron mi tarjeta. |

`lançamento` is the pt-BR word for a statement line used elsewhere in the set
(`txWord`), and it is understood as a charge; `cobrança` is the charge word. No
row drifted in meaning. The not-mine rows keep the explicit "not me" claim that
sets `states_not_theirs`, which is what makes the `fraud.claim` rule fire.
