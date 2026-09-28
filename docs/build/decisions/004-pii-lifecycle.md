# 004 · PII masking and unmasking lifecycle

**Date:** 2026-09-28
**Status:** Proposed
**Participants:** Natalia Restrepo, Rubén Dorta

## Context

Personal data must never reach the LLM or the browser (REQ-0047, no identifiers in the LLM; REQ-0031, approved data only; REQ-0027, access control and retention). PII appears in two planes: at rest in the lakehouse and in flight in live chat. Each plane needs its own masking mechanism, with a clear owner per plane. Proposed by Natalia (9/28); the static half is already noted in [security](../security.md#data).

## Options

1. **Two-plane masking (proposal):** static redaction/hashing in the Silver layer (data engineering) plus dynamic per-message masking with a session token vault and re-hydration at tool-call time (AI/full-stack). Full coverage, but more pieces to build and a session vault to secure.
2. **Session isolation only:** rely on per-customer tool filtering and never sending identifiers to the LLM, without a token vault. Simpler, but raw PII in user messages still travels further before it is contained.
3. **Static masking only:** clean the lakehouse and trust prompt-level rules for live chat. Weakest against injection and prompt leakage.

## Decision

We propose option 1 (two-plane masking). Static masking lands in the Silver layer; dynamic masking (Regex + NER, e.g. Microsoft Presidio or SpaCy) intercepts live prompts, replaces PII with session tokens, and re-hydrates tokens only inside parameterized tool calls. Final confirmation pending implementation capacity.

## Consequences

- What we gain: defense in depth across batch and real-time; the LLM only ever sees anonymized prompts; analysts and batch ML never see raw credentials.
- What we sacrifice: we must build and secure the session vault, define its retention, and keep the re-hydration path out of logs.
- Pending: tooling choice (Presidio vs Regex/SpaCy), vault retention policy, adversarial coverage of the masking path (with [ML](../areas/ml.md), REQ-0021), and the storage decision it partially depends on (decision 12).
