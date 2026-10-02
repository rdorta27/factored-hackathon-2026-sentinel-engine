# 017 · Portuguese without Portuguese data

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 15. Conversation rules: [languages](../conversation.md#languages).

## Context

The brief requires interactions in Spanish and Portuguese (REQ-0012, P0) and the video should show a Portuguese case (REQ-0009). The dataset has no Portuguese text and no Brazilian accounts: `customers.country` is México, Colombia or Argentina only ([dataset assumptions](../../understand/dataset.md#assumptions)). The current Portuguese material is 13 single-turn utterances that only exercise the router. Nobody on the team speaks Portuguese.

## Options

1. **External Portuguese data:** allowed if justified (REQ-0054), but it would bring complaints about Brazilian accounts the system does not hold, and needs license and PII review. Dropped earlier.
2. **A Brazilian market:** no data supports it.
3. **Portuguese as a customer language on existing accounts, with team-written cases checked through Spanish.**

## Decision

Option 3.

- **Who writes in Portuguese:** a customer of México, Colombia or Argentina. The reply is in pt-BR; currency, policy and thresholds follow the account (this is how the code already works). Brazilian terms such as Pix, extrato or CPF are understood and answered with the account's real data.
- **Test cases:** every important es-419 case gets a pt-BR twin, including the three demo cases (normal through confirmation, ambiguous, human) and multi-turn cases. All are labeled team-written simulation and kept in the development split, except a pt-BR block in the next held-out set measured once.
- **Review without speakers:** each pt-BR case is written by one model and back-translated to Spanish by a different model; the team checks the back-translation against the intended Spanish case (meaning, amount, merchant, intent) and fixes or drops any case that drifts. Brazilian banking terms are checked against the [pt-BR glossary](../../understand/glossary/glossary.pt-br.md).
- **Reporting:** metrics by language with n; if pt-BR does worse, the cause is stated, not hidden.

## Consequences

- The team can verify every Portuguese case in a language it reads, which a single model review would not allow.
- Fluency is not verified by a native speaker: the submission says so (REQ-0013), and the review method is part of the presentation.
- The router's strong route ([016](016-router-models.md)) handles Portuguese turns, and the selection rule already requires no more than a 5-point drop in pt-BR.
- For the held-out measurement of [018](018-evaluation-acceptance.md), the team-member check was replaced by an isolated model review, by the owner's choice; 018 records who wrote and reviewed each part.
