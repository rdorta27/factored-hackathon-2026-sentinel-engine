---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 017 · Portuguese without Portuguese data

**Date:** 2026-10-01
**Status:** Accepted
**Participants:** Rubén (owner)

Closes pending decision 15. Conversation rules: [languages](../conversation.md#languages).

## Context

The brief requires interactions in Spanish and Portuguese (REQ-0012, P0). The video must show a Portuguese case (REQ-0009). The dataset has no Portuguese text and no Brazilian accounts: `customers.country` is México, Colombia or Argentina only ([dataset assumptions](../../data/dataset.md#assumptions)). The Portuguese material at that date was 13 single-turn messages that test only the router. Nobody on the team speaks Portuguese.

## Options

1. **External Portuguese data:** permitted with a justification (REQ-0054). It brings complaints about Brazilian accounts that the system does not have, and it needs a license and a PII review. Dropped before.
2. **A Brazilian market:** no data supports it.
3. **Portuguese as a customer language on the existing accounts, with team-written cases checked through Spanish.**

## Decision

Option 3.

- **Who writes in Portuguese:** a customer of México, Colombia or Argentina. The reply is in pt-BR. The currency, the policy and the thresholds follow the account, as the code already does. The system understands Brazilian terms such as Pix, extrato (statement) or CPF (Brazilian tax id), and answers with the real data of the account.
- **Test cases:** each important es-419 case gets a pt-BR twin. This includes the three demo cases (normal case through the confirmation, ambiguous case, human case) and multi-turn cases. All are labelled team-written simulation and stay in the development split. The exception is a pt-BR block in the next held-out set, measured once.
- **Review without speakers:** one model writes each pt-BR case. A different model translates it back to Spanish. The team compares the back-translation with the intended Spanish case (meaning, amount, merchant, intent). The team fixes or drops a case that drifts. The [pt-BR glossary](../../glossary/glossary.pt-br.md) checks the Brazilian banking terms.
- **Reporting:** metrics per language with n. If pt-BR is worse, we state the cause. We do not hide it.

## Consequences

- The team can verify each Portuguese case in a language that it reads. A review by one model does not allow this.
- No native speaker verifies the fluency. The submission says so (REQ-0013), and the presentation shows the review method.
- The strong route of the router ([016](016-router-models.md)) handles Portuguese turns. The selection rule already permits no more than a 5-point drop in pt-BR.
- For the held-out measurement of [018](018-evaluation-acceptance.md), an isolated model review replaced the check by a team member, by the choice of the owner. Decision 018 records who wrote and reviewed each part.
- *Updated 10/4:* the dataset transcripts are two Spanish templates. A 2% replay sent all 280 sampled openings to a handoff ([`transcript-chats/20261002T144836Z`](../../../evidence/transcript-chats/20261002T144836Z/summary.json)). They are not a source of customer language in any locale.
