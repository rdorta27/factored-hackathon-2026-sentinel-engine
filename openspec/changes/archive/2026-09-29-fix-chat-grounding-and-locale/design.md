# Design: fix-chat-grounding-and-locale

## Context

See proposal.md (Why). Current state: the mock orchestrator keyword-routes a message straight to a transaction reference and the disputes service opens a case from whatever Gold row that reference names, with no comparison against the customer's words. Eligibility uses a hardcoded simulated date (`DEMO_TODAY = 2026-06-20`) that is never shown. One mock customer (`CUST-0001`) with MXN rows; the UI renders ISO timestamps and passes several strings through raw keys.

## Goals / Non-Goals

**Goals:**

- Make "did the customer describe a real transaction?" a decidable, testable step that runs before any creation.
- Keep every value (currency, amount, date) owned by data, with language confined to presentation.

**Non-Goals:**

- No natural-language date parsing beyond the demo's stated formats, no fuzzy merchant matching, no LLM in the grounding step. Phase 2 may replace the parser, not the rule.

## Decisions

- **Grounding as a resolve step with three outcomes: matched, ambiguous, none.** `resolve_transaction(stated, candidates)` returns exactly one candidate only on exact agreement of date, amount, and merchant after normalization (case-folding, accent-stripping, thousands/decimal separators). Two or more surviving candidates stay ambiguous by definition, which is what makes the bug reproducible in a test. Alternative rejected: trust the keyword router's reference, which is the bug.
- **Candidates instead of silence.** The `clarification` reply gains a `candidates` list (date, amount, currency, merchant, reference) so the interface can render chips and the customer can pick. Choosing a candidate is the explicit-election path the spec allows. Alternative rejected: a free-text "which one?" that restarts the ambiguity.
- **Reference date from `SENTINEL_REFERENCE_DATE`.** One environment variable (default `2026-06-17`, the dataset's last date) flows into `DisputePolicy`, the UI header, and the receipt. The default is not arbitrary: with the real clock nothing in a static dataset is inside a 90-day window, so the demo would refuse every charge. Tests pin days 89/90/91 as the boundary contract rather than asserting today's behavior. Alternative rejected: `date.today()`, which makes the demo date-dependent and non-reproducible.
- **Bilingual grounding through one normalizer.** A single `parse_statement(message, locale_hint)` extracts optional date, amount, and merchant using Spanish and Portuguese month tables, both dispute words (`cargo`, `cobro`, `cobrança`, `reclamo`), and both amount conventions (`1.000,00` and `1,000.00`), resolving the separator convention by which one appears last. The same normalizer feeds the comparison, so a Portuguese message and a Spanish message about the same charge produce identical candidate sets. Alternative rejected: two per-language parsers, which drift apart.
- **Branding stays out.** Visual design is a separate change (`adopt-team-branding`) that reads the team's `branding/` folder, which is not on `main` in this checkout yet. This change adds functional UI only (panel, chips, states, reference-date line, localization) on the existing minimal stylesheet, so the two changes do not collide in the same files.
- **Amount-hold field removed, not renamed.** A rename keeps the concept alive in the payload; removing it and stating "no funds held" in the receipt is the only honest reading of REQ-0004. The mock already simulates actions only.
- **Mutation for locale switching; formatting keys for values.** A `format` object carries `dateDisplay`, `amountDisplay`, and `currency` pre-formatted on the server where the locale is known, and the client re-formats with `Intl.NumberFormat`/`Intl.DateTimeFormat` when the user switches language. Currency value never changes, only its rendering. Alternative rejected: formatting client-side only, which would hide the account-owned currency from the payload contract.
- **Per-country Gold customers.** Each country customer gets rows in its own currency and its own dates, with the MX set keeping the existing references so current tests stay meaningful. The customer record carries `country`, which sets the default locale in the UI.
- **i18n completeness as a test, not a habit.** A test enumerates the keys the card and shell render and fails listing any locale missing them, plus a check that no raw key literal appears in the JS render functions. This is deterministic and catches the next leak, not just today's.
- **Transaction panel as the primary disambiguation.** Listing the customer's charges with tap-to-dispute attacks the ambiguity at the source: the customer never has to describe a transaction in prose. The panel reads the same listing endpoint the candidate chips use.

## Contract change for the orchestrator (share with Rubén)

`app/chat/contract.py` is imported by the mock today and by the real
orchestrator in Phase 2. **The contract changed twice** (first for the
Proof-of-Work fields, then for localization); the tables below are the final
shape as implemented and tested. Nothing in the interface writes prose any
more: the payload carries **raw values and translation keys**, and the client
formats and translates.

### `POST /chat` request

| Field | Type | Notes |
|---|---|---|
| `message` | `str`, optional, ≤2000 | Customer words. Default empty so a pure selection is valid. |
| `selected_reference` | `str \| null`, pattern `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$` | Explicit choice from the UI. Format-neutral **on purpose**: Phase 2 ids are `VARCHAR(30)` and will not look like the mock's `TXN-1234`. Authorization comes from the session-scoped row lookup, not the pattern. |

`extra="forbid"` on the body: `customer_id` in the body is still a 422.

### `CaseConfirmation` (final shape)

| Field | Type | Change in this change |
|---|---|---|
| `kind` | `Literal["case_confirmation"]` | unchanged |
| `case_id` | `str` | unchanged (server-generated, safe to display) |
| `transaction` | `TransactionFacts` (`amount`, `currency`, `merchant`, `date`) | `date` is ISO `YYYY-MM-DD`; the client formats |
| `state` | `str` | unchanged |
| `priority` | `str` | unchanged |
| `verified_at` | `datetime` | unchanged |
| `verified` | `Literal[True]` | unchanged; re-read proof |
| `display` | `ConfirmationDisplay` | **added** |
| `messages` | `MessageKeys` | **added** |
| `source` | `Literal["mock","live"]` | unchanged |
| `hold` | — | **removed**: never claim money movement (REQ-0004) |
| `no_funds_held` | — | **removed**: replaced by `messages.noFunds`, so the client owns the wording |
| `eligibility` | — | **removed**: replaced by `messages.rule` |
| `queue_status` | — | **removed**: replaced by `messages.queue` |
| `receipt_ref` | — | **removed**: the client derives the download from `case_id` |
| `next_steps` | — | **removed**: replaced by `messages.nextStep` plus `display.slaDate` |
| `expected_timeline` | — | **removed**: "2 business days" was English prose; the date now comes from `display.slaDate` |

`ConfirmationDisplay`: `amount` (raw string), `currency` (ISO code, always shown),
`merchant` (customer data, never translated), `referenceDate`, `slaDate` (both ISO).

`MessageKeys`: `nextStep`, `rule`, `queue`, `noFunds` — each a key the client
resolves in its locale.

### `Clarification` (final shape)

| Field | Type | Notes |
|---|---|---|
| `kind` | `Literal["clarification"]` | unchanged |
| `message_key` | `str` | **replaces `text`**: the question is translated client-side |
| `missing` | `str` | which datum is missing |
| `candidates` | `list[CandidateTransaction]`, **max 4** | **added**, ranked, may be empty |

`CandidateTransaction`: `reference` (internal id — data for the request body,
**never rendered**), `amount`, `currency`, `merchant`, `date`, plus `eligible: bool`
and `ineligibleKey: str | None` so the UI can disable an out-of-window chip and
say why.

### Other reply kinds

| Kind | Change |
|---|---|
| `TextReply` | `text` **replaced by** `message_key` |
| `ErrorReply` | `message` **replaced by** `message_key`; `trace_id` unchanged |
| `Handoff` | `reason` **replaced by** `reason_key` (+ optional `reason_detail`); `advisor_received` and `estimated_time` **removed** (server-authored English); `estimated_date` added; `reference` unchanged |

### `POST /api/v1/disputes/create` (final shape)

Same `display` + `messages` treatment. Refusals return `reason_key` +
optional `reason_detail` instead of prose; the failure path returns
`reason_key` plus `handoff.reference`.

**Required fields are intentional.** A Phase 2 orchestrator still emitting
`hold`, `text`, `eligibility`, or `reason` fails loudly at validation instead of
silently shipping English to a Spanish-speaking customer.

## Risks / Trade-offs

- [Risk] Stricter grounding breaks the existing demo keyword paths → Mitigation: the mock emits statements that match its rows exactly, and the suite proves each scenario still resolves.
- [Risk] Normalization is easy to over-tune (fuzzy matching reintroduces the bug) → Mitigation: normalization limited to whitespace, case, accents, and separators; no edit distance.
- [Risk] Adding a candidates list changes the `clarification` payload → Mitigation: additive field with a default empty list; existing tests assert `missing` only.
- [Risk] Removing the hold field breaks contract tests → Mitigation: intentional break, listed as a task, and the contract test is updated to assert its absence.
- [Risk] Locale defaulting per country could surprise a reviewer who picks another language → Mitigation: selection persists for the session and the selector always wins.

## Migration Plan

1. Land grounding plus the `SENTINEL_REFERENCE_DATE` variable with tests; existing chat paths are re-pointed to exact-match statements.
2. Land per-country Gold rows and the currency-formatting contract; keep the MX references stable.
3. Land the functional UI additions (panel, chips, states, reference-date line) and complete localization; then the i18n completeness test.
4. After `branding/` reaches `main`, `adopt-team-branding` restyles these screens against the team tokens — no further contract change.
5. Rollback: the grounding step is one function; reverting it restores the previous routing without touching the seam.

## Open Questions

- None that change specs or tasks. Bank-grade name display (which parts of a real name may be shown) stays with decision 004 on PII and is out of scope for the mock.
