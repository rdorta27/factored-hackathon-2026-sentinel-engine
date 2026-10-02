# Conversation

How the assistant behaves with the customer, organized by situation, and how it handles Spanish and Portuguese. It is the basis of the demo and the video.

**Purpose:** decide what the assistant says and does in each situation. **Related:** [system](../architecture/system-architecture.md), [security](security.md), [requirements](../requirements/requirements.md).

## Principles

- **AI understands; code executes and verifies** (see [system](../architecture/system-architecture.md#central-principle)).
- **Autonomy by risk:** actions with consequences (blocking, opening a dispute) ask for confirmation (REQ-0006, autonomy rules).
- **Only verified facts;** if the data does not exist, say so and offer an alternative. Never answer with the model's own knowledge (REQ-0003, verified records).
- **Separate what is verified from what the customer states.**
- **Only report actions confirmed** by the tool; timeout is not success (REQ-0005, verified actions).

## When data is not up to date

REQ-0039 (declare freshness). If the customer mentions something more recent than the data, do not claim it is visible:

> "Mis registros están actualizados hasta hoy a las 00:00 y todavía no veo ese cobro. Puedo abrir el reclamo ahora como pendiente de verificación; se confirmará en la próxima actualización. ¿Lo abro?"
> ("My records are updated as of today at 00:00 and I still don't see that charge. I can open the dispute now as pending verification; it will be confirmed in the next update. Shall I open it?")

## When information is missing

REQ-0002 (clarify or abstain). Ask only what is essential. When possible, **show verified options** instead of asking the customer to type data.

## When opening a dispute

REQ-0042 (minimum effort) and REQ-0043 (check the charge status).

1. Search the session customer's candidate transactions.
2. Check the status: **Pending** may be a pre-authorization that clears on its own (offer to wait or file the dispute); **Reversed** means it was already refunded.
3. Show the candidates and let the customer choose:
   > "Veo estas compras repetidas en los últimos 7 días:
   > 1. Supermercado Éxito, 85.000 COP, 25/09, tarjeta de débito •••4521
   > 2. Rappi, 32.500 COP, 24/09, tarjeta de crédito •••7788
   > ¿Cuál quieres reclamar?"
   > ("I see these repeated purchases in the last 7 days:
   > 1. Éxito supermarket, 85,000 COP, 09/25, debit card •••4521
   > 2. Rappi, 32,500 COP, 09/24, credit card •••7788
   > Which one do you want to dispute?")
4. Two identical charges can be legitimate: show the facts without concluding there was an error.
5. If it does not appear, ask for the minimum and open the dispute as **pending verification**.
6. Ask for confirmation before opening it; report the case number only when the tool confirms it.

## When the customer asks to speak to a person

REQ-0040 (advisor request). The policy in code decides, not the predictor or the LLM.

- A single offer: "Puedo ayudarte con esto ahora mismo. ¿Prefieres intentarlo conmigo o que te comunique con un asesor?" ("I can help you with this right now. Would you prefer to try it with me or that I connect you with an advisor?")
- If they repeat or choose the advisor: escalate immediately, without insisting.
- Log each request: many requests at the same step signal a flow problem.

## App context

REQ-0045 (recent app errors, only as auxiliary context: app diagnosis is not a flow in the challenge statement). If there is a recent error (e.g., a failed transfer — SPEI, the Mexican instant-transfer system — or Pix, the Brazilian instant-payment system), offer it as a question: "¿Tu consulta tiene que ver con la transferencia que falló ayer?" ("Is your question about the transfer that failed yesterday?"). Never assert it or surprise the customer.

## Language

REQ-0044 (neutral Spanish (es-419)) and REQ-0041 (original currency). The account's country does not say where the customer is from (e.g., a Venezuelan in Colombia).

- Neutral, clear Spanish, with no single-country slang.
- Explain acronyms and local terms on first use (e.g., "SPEI, Mexico's instant-transfer system").
- Understand other countries' terms ("pago móvil", the Venezuelan mobile-payment system; "Pix", the Brazilian instant-payment system) and respond with what does exist at their bank.
- The response language follows the customer; the currency follows the account (see [languages](#language-country-and-currency-are-independent)).
- Per-country equivalences in the [glossary](../understand/glossary/).

## Languages

### Challenge requirements

- **Robust** interactions in Spanish and Portuguese. The kickoff marks this as mandatory.
- Report data and language-coverage limitations.
- Exact parity is not required, but metrics must be split by language and differences investigated.

### Main risk

**We are given no Portuguese data to build with** (the dataset confirms it: all text is in Spanish, with Mexican, Colombian, and Argentine variants; no Lusophone country), but evaluators will likely still test in PT, like a hidden test set.

### Strategy

- We prefer **multilingual** components (LLM, multilingual embeddings) over models trained only on Spanish.
- Deterministic logic does **not depend on language**: no Spanish-only keywords.
- We create our own pt-BR test cases (translated, synthetic, or drawn from external Brazilian complaint data), **labeled as such** and **held back**: we do not use them to tune the system. External data is allowed if justified (help channel, 9/28; REQ-0054).
- We put pt-BR in the adversarial set (injection, multilingual ambiguity).

### Language, country, and currency are independent

A customer may write in Portuguese and hold their account in MX, CO, or AR.

- The **response language** follows the customer.
- The **currency** follows the account or transaction (MXN, COP, ARS, or USD); it is never converted to match the language.
- We split metrics by language **and** by country.

### Brazilian Portuguese

Portuguese tests are most likely to be from Brazil (pt-BR). The customer may use terms from the Brazilian system (Pix, extrato — statement; estorno — refund/chargeback; atendente — advisor; CPF, Cadastro de Pessoas Físicas, the Brazilian individual taxpayer ID) even if their account is in MX, CO, or AR. The assistant must understand them but respond with the account's real data (for example, there is no Pix in the dataset). Equivalences in the [glossary](../understand/glossary/glossary.pt-br.md).

### Spanish variants

The dataset includes accent-detection fields (Mexican, Colombian, Argentine and, in `customers`, neutral). They serve as segments to measure fairness within Spanish.

### Reporting

- Metrics by language, with n.
- If pt-BR performs worse, we explain the cause (e.g., no pt-BR training data); we do not hide it.

### Generating and validating pt-BR cases

Nobody on the team speaks Portuguese, so cases are checked through Spanish: one model writes the pt-BR case, a different model back-translates it, and the team compares the back-translation with the intended Spanish case. Every important es-419 case has a pt-BR twin ([017](decisions/017-portuguese.md)).
