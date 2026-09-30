# Proposal: fix-chat-grounding-and-locale

## Why

Demo testing found unsafe outcomes: the assistant opened a case on a transaction the customer never described, treated a 125-day-old charge as eligible, and showed card details with raw ISO dates and untranslated labels. Under the evaluation rubric these are unsafe automated resolutions, not cosmetic defects, so they are fixed before any design polish.

## What Changes

- Transaction grounding: a case SHALL open only when the customer's stated date, amount, and merchant match a Gold row exactly, or when the customer explicitly picks one of the presented candidates. Every other case returns `clarification` with the candidate list. No inferred or default transaction ever reaches creation. Grounding SHALL work for Spanish and Portuguese messages, including month names, `cobrança`/`cargo`, and regional amount formats (`1.000,00` and `1,000.00`).
- Explicit reference date: one environment variable, `SENTINEL_REFERENCE_DATE` (default `2026-06-17`, the last date in the dataset, because the real clock would make nothing eligible), becomes the system "today"; it is displayed in the UI and the receipt, and feeds the 90-day check. Tests cover days 89, 90, and 91.
- Currency from the account, never the language: the transaction carries its own currency. Locale affects formatting only (`Intl.NumberFormat`, `Intl.DateTimeFormat`), never the value. Per-country mock customers (MX/MXN, CO/COP, AR/ARS) with coherent transactions; the UI starts in the language matching the customer's country and stays switchable.
- Functional interface work only: candidate quick-reply chips, a transactions panel where tapping a charge starts that dispute, a visible reference-date line, and complete localization. Visual restyling is deferred to a separate change (`adopt-team-branding`) that consumes the team's `branding/` folder as the single source of truth.
- Complete i18n: every visible string, including all receipt-card details, comes from the translation files; no English leak and no raw keys such as `hold`/`rule`/`ref`. Dates render per locale, never ISO. A test fails when any card string is missing in `es-419`, `es-MX`, `es-CO`, `es-AR`, or `pt-BR`.
- Amount hold removed from the customer card: the challenge does not authorize moving money. The card states in text that no funds are frozen and the case is a simulation.
- `/` redirects to `/ui/`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `chat`: grounding rule, candidate clarification, bounded retries keep applying only after a confirmed transaction.
- `disputes`: explicit reference date plus day-89/90/91 boundaries, currency sourced from the account, hold removed from the customer-facing payload.
- `gold-layer`: per-country mock customers and coherent multi-currency rows.
- `chat-ui`: customer-visible redesign (bank header, secure-session indicator, masked name, transaction side panel with tap-to-dispute, quick-reply chips, typing states, clearer receipt hierarchy, mobile layout) plus full localization and locale-aware formatting.

## Impact

- Code: `sentinel-login/` only (`app/chat/`, `app/disputes/`, `app/gold/`, `app/ui/`). No new dependencies; locale formatting uses the JavaScript platform APIs.
- API: `POST /chat` keeps its five reply kinds; `clarification` gains a candidate list. `CaseConfirmation` loses the hold field and gains a localized, formatted display section — shared with Rubén's orchestrator, which imports `app/chat/contract.py`.
- Environment: new `SENTINEL_REFERENCE_DATE` variable, documented in the package README with the reason for its default.
- UI: functional additions only (chips, transactions panel, reference-date line, localization). Visual design stays with the team's `branding/` folder and the later `adopt-team-branding` change.
- Tests: the 88 existing tests stay green; new suites cover grounding in Spanish and Portuguese (including a Portuguese ambiguous case), the three date boundaries, currency/locale independence, i18n completeness, hold removal, and the `/` redirect.
- Traces to REQ-0003, REQ-0005, REQ-0041, REQ-0042, REQ-0044, REQ-0012, REQ-0004; builds on `docs/build/conversation.md` and decisions 003/006.

## Non-goals

- No real banking integration, no money movement of any kind, and no change to the Phase 2 seams.
- Language detection from message text is not added: the locale follows the customer's country and the explicit selector.
- Visual redesign, brand tokens, and typography are out of scope; they belong to `adopt-team-branding` after `branding/` lands on `main`.
