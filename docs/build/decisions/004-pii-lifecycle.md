---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 004 · Personal data (PII) masking and unmasking lifecycle

**Date:** 2026-09-28
**Status:** Partially accepted (9/29): option 2 is the built baseline; the option 1 additions stay proposed
**Participants:** Natalia Restrepo, Rubén Dorta

## Context

PII must never reach the LLM or the browser (REQ-0047, no identifiers in the LLM; REQ-0031, approved data only; REQ-0027, access control and retention). PII is in two planes:

- At rest, in the lakehouse.
- In flight, in the live chat.

Each plane needs its own masking mechanism and one owner. Natalia proposed this on 9/28. The static half is already in [security](../security.md#data).

## Options

1. **Two-plane masking (proposal):**
   - Static redaction or hashing in the Silver layer (data engineering).
   - Dynamic masking of each message with a token vault per session. Code unmasks a token only inside a tool call (AI and full-stack).
   - Full coverage, but more parts to build and a token vault to secure.
2. **Session isolation only:** the tools filter by customer and never send identifiers to the LLM. No token vault. Simpler, but raw PII in a customer message travels further before code contains it.
3. **Static masking only:** clean the lakehouse and trust rules in the prompt for the live chat. The weakest option against injection and prompt leakage.

## Decision

We propose option 1 (two-plane masking):

- Static masking is in the Silver layer.
- Dynamic masking (regex and NER, for example Microsoft Presidio or SpaCy) reads each live prompt, replaces PII with session tokens, and unmasks them only inside parameterized tool calls.
- **Mask** means: replace a personal value with a token before it reaches the LLM or the logs. **Unmask** means: code puts the real value back in place of the token, only inside a tool.
- **An unmasked value is never a lookup key.** Every tool reads by the `customer_id` of the session. Code can compare a token only with the data of that customer (for example, the last four digits of the card). A lookup by an identifier typed in the chat would let anyone read the data of another customer.

The final confirmation depends on the capacity to implement it.

## Update 9/29

The architecture ([personal data](../../architecture/specification.md#personal-data)) builds **option 2** as the baseline: data minimization at three boundaries, all in code.

- The service reads a Gold view without personal columns (agreed with the data owner).
- The tools return only the fields that the reply needs.
- The logs hold no customer text and no `customer_id`.

The two option 1 additions are not built for the submission. They stay proposed:

- **Token vault** for what the customer types: build it, or declare it as a limit. This is an open team question. The flow does not need the national id of the customer, because the session identifies the customer.
- **Static masking in Silver:** not implemented in `transform_silver.py`.

The demo stated the gap: the text that the customer types reached the LLM unmasked. *Later update:* code now masks free customer text by pattern before any model call (REQ-0047). Attack A9 checks that a national id never reaches the model ([adversarial run](../../../evidence/adversarial/20261002T222323Z/summary.json)). Personal data outside those patterns is not detected.

## Consequences

- Gain: defense in depth for batch and real time. The LLM sees only anonymized prompts. Analysts and batch ML never see raw credentials.
- Cost: we must build and secure the token vault, define its retention, and keep the unmask path out of the logs.
- Silver does not hash the credit score and the income: ML and analysis need them as features. Open: how we restrict access to them.
- Open: the tool (Presidio or regex and SpaCy), the retention policy of the token vault, and the adversarial coverage of the masking path (with [ML](../areas/ml.md), REQ-0021). The data storage decision (decision 12) is closed: a Delta Lakehouse (DuckDB locally, Azure Databricks in production). Static Silver masking runs in the same `sentinel_data` package through `transform_silver.py`.
