# Spec Delta

## REMOVED Requirements

### Requirement: Policy-gated dispute creation

**Reason**: A REST create (`POST /api/v1/disputes/create`) is a second write path that skips the confirm box. No requirement asks for a disputes API; the brief asks for confirmation before actions and verified outcomes only (REQ-0006, REQ-0005).
**Migration**: Disputes open only through `POST /api/v1/chat` after the confirm box, with the policy engine deciding (`chat` "Message-only chat request", `dispute-confirmation`). Eligibility, refund and prior-dispute checks stay in the policy engine; idempotency stays on the tool port.

### Requirement: Proof-of-Work payload

**Reason**: It required a resolution deadline, a downloadable receipt and a queue status, which contradicts `chat` "Verify-before-claim confirmations" (no SLA, queue or receipt).
**Migration**: Use `case_confirmation`: case id, transaction facts, `verified_at`, reference date, rule key, no-funds key, `source`.

### Requirement: Business-day resolution deadline

**Reason**: The deadline existed for the Proof-of-Work card and receipt, both removed.
**Migration**: None. A handoff may show an estimated date; confirmations do not claim a deadline.
