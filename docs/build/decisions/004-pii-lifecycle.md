# 004 · Personal data (PII) masking and unmasking lifecycle

**Date:** 2026-09-28
**Status:** Proposed
**Participants:** Natalia Restrepo, Rubén Dorta

## Context

PII must never reach the LLM or the browser (REQ-0047, no identifiers in the LLM; REQ-0031, approved data only; REQ-0027, access control and retention). PII appears in two planes: at rest in the lakehouse and in flight in live chat. Each plane needs its own masking mechanism, with a clear owner per plane. Proposed by Natalia (9/28); the static half is already noted in [security](../security.md#data).

## Options

1. **Two-plane masking (proposal):** static redaction/hashing in the Silver layer (data engineering) plus dynamic per-message masking with a per-session token vault, unmasked only inside tool calls (AI/full-stack). Full coverage, but more pieces to build and a token vault to secure.
2. **Session isolation only:** rely on per-customer tool filtering and never sending identifiers to the LLM, without a token vault. Simpler, but raw PII in user messages still travels further before it is contained.
3. **Static masking only:** clean the lakehouse and trust prompt-level rules for live chat. Weakest against injection and prompt leakage.

## Decision

We propose option 1 (two-plane masking). Static masking lands in the Silver layer; dynamic masking (Regex + NER, e.g. Microsoft Presidio or SpaCy) intercepts live prompts, replaces PII with session tokens, and unmasks them only inside parameterized tool calls. **Mask** means replacing a personal value with a token before it reaches the LLM or the logs; **unmask** means code swapping the token back for the real value, only inside a tool. **An unmasked value is never a lookup key:** every tool reads by the session's `customer_id`, and a token can only be compared against that customer's own data (e.g. the last four digits of their card). Looking up by an identifier typed in the chat would let anyone read another customer's data. Final confirmation pending implementation capacity.

## Consequences

- What we gain: defense in depth across batch and real-time; the LLM only ever sees anonymized prompts; analysts and batch ML never see raw credentials.
- What we sacrifice: we must build and secure the token vault, define its retention, and keep the unmasking path out of logs.
- Credit score and income are not hashed in Silver: ML and analysis need them as features. Pending: how we restrict access to them.
- Pending: tooling choice (Presidio vs Regex/SpaCy), token vault retention policy, adversarial coverage of the masking path (with [ML](../areas/ml.md), REQ-0021), and the storage decision it partially depends on (decision 12).
