# Decision-explanation review (pt-BR)

Back-translation of the `explanation.*` locale texts added for the why
follow-up, signed by a model other than the writer, as in
[017](../../../docs/build/decisions/017-portuguese.md). A row is OK only if the
meaning survives; the placeholders are kept literal so the reviewer checks the
sentence, not the rendering.

| Field | Value |
|---|---|
| Writer | grok-4.7 |
| Back-translator | fireworks-ai/accounts/fireworks/models/deepseek-v4p1-flash |
| Reviewer model | fireworks-ai/accounts/fireworks/models/deepseek-v4p1-flash |
| pt-BR signed | yes, 2026-10-02 |

The three safety rules share one sentence (`explanation.safety`) on purpose, so
there is one row for all three. The neutral `rule_id` (`advisor.review`) is not
translated; it is an internal code the page does not render.

| OK | Key | Intended Spanish | pt-BR | Back-translation |
|---|---|---|---|---|
| [x] | `explanation.window.expired` | Te explico la regla que apliqué: para reclamar un cargo hay un plazo de {window_days} días desde la fecha del cargo. Este cargo es del {charge_date}, así que la última fecha para reclamar fue el {last_eligible_date}. | Vou explicar a regra que apliquei: para contestar uma cobrança existe um prazo de {window_days} dias a partir da data da cobrança. Esta cobrança é de {charge_date}, então a última data para contestar foi {last_eligible_date}. | Te explico la regla que apliqué: para disputar un cargo existe un plazo de {window_days} días a partir de la fecha del cargo. Este cargo es de {charge_date}, así que la última fecha para disputar fue {last_eligible_date}. |
| [x] | `explanation.status.pending` | Te explico la regla que apliqué: el cargo sigue pendiente, así que todavía no se puede reclamar. | Vou explicar a regra que apliquei: a cobrança ainda está pendente, então ainda não pode ser contestada. | Te explico la regla que apliqué: el cargo todavía está pendiente, así que todavía no puede ser disputado. |
| [x] | `explanation.status.reversed` | Te explico la regla que apliqué: el cargo ya fue reversado, así que no hay nada que reclamar. | Vou explicar a regra que apliquei: a cobrança já foi estornada, então não há o que contestar. | Te explico la regla que apliqué: el cargo ya fue reversado, así que no hay nada que disputar. |
| [x] | `explanation.status.declined` | Te explico la regla que apliqué: el cargo fue rechazado y no se cobró, así que no hay nada que reclamar. | Vou explicar a regra que apliquei: a cobrança foi recusada e não houve débito, então não há o que contestar. | Te explico la regla que apliqué: el cargo fue rechazado y no hubo débito, así que no hay nada que disputar. |
| [x] | `explanation.already.disputed` | Te explico la regla que apliqué: ese cargo ya tiene un reclamo abierto. | Vou explicar a regra que apliquei: essa cobrança já tem uma contestação aberta. | Te explico la regla que apliqué: ese cargo ya tiene una disputa abierta. |
| [x] | `explanation.safety` | Un asesor revisa tu caso y te dará una respuesta. No puedo darte más detalles sobre cómo se decide. | Um atendente vai analisar o seu caso e dar uma resposta. Não posso dar mais detalhes sobre como isso é decidido. | Un asesor va a analizar su caso y dar una respuesta. No puedo dar más detalles sobre cómo eso se decide. |
| [x] | `explanation.demo` | Esta es la política de demostración del servicio, no la regla de un banco. | Esta é a política de demonstração do serviço, não a regra de um banco. | Esta es la política de demostración del servicio, no la regla de un banco. |
| [x] | `explanation.none` | Puedo ayudarte con un cargo que no reconozcas. Cuéntame cuál es. | Posso ajudar com uma cobrança que você não reconheça. Me diga qual é. | Puedo ayudar con un cargo que usted no reconozca. Dígame cuál es. |

No row drifted in meaning. `contestar`/`disputar` are the pt-BR and es-419
verbs for the same action; `estornada`/`reversado` are the reversal terms used
elsewhere in each locale.
