---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

The judges score the product and the pitch more than the code: slides are 60% product, the video is 90% product. The page must look like part of a bank, and the [design canvas](https://claude.ai/artifact/U8CtkRi6b5zBLRkc5iXzuZ) "Sentinel Engine UI" shows the target. PR #57 (`ui-product`) built the demo entry, the "Cómo lo resolví" ("How I resolved it") panel and the advisor trace, but not these parts of the canvas:

- A bank shell: bank name, masked card, country and language, data as-of date.
- The status of each recent charge: eligible, in review, with an advisor, already disputed, outside the window. Felix asked for the same (his points 1 and 5).
- The handoff card inside the thread, with the request, the verified facts, the actions, the reason and what is pending. Diego asked that the advisor always see why.
- A phone layout (Felix point 10) and the "why I decided this" card.
- The white-label promise of the slides ("your brand, our trust layer"): today it is only a placeholder.

Cuentas y saldos (accounts and balances) stay out. The data cannot support a balance ([investigation data support](../../../docs/rationale/investigation-data-support.md)), and decision 008 keeps one flow.

## What Changes

- **API:** `GET /api/v1/transactions` adds a `case_state` per charge from the case store: `eligible`, `in_review`, `with_advisor`, `already_disputed`, `outside_window`, `not_disputable`. No new personal field.
- **Bank shell:** header with the configured bank name and accent color, the masked product of the session (type and last four digits only), country, language and the as-of date. No balance.
- **Three columns on desktop:** "What we checked" (the turn steps), the thread, and the recent charges with their state. One column on a phone, with the steps behind a button.
- **Handoff card in the thread:** request, verified facts, actions, reason, pending.
- **White label:** `SENTINEL_BRAND_NAME` and `SENTINEL_BRAND_ACCENT` set the name and the accent. Defaults: "Sentinel" and the current brand. Contrast is checked.
- **Entry:** the promises and the four test-case cards with tag, language and story, as in the canvas. The demo banner stays.
- **Screens:** regenerate `docs/build/screenshots/ui-product/` with `scripts/capture_ui_product.py`.
- **Advisor view stays read-only** (decision 009). The canvas buttons "Take case" and "Mark resolved" are not built; the roadmap lists them.
- **Human review G1:** the owner reviews the look on desktop and phone. Several rounds are expected, so styles stay in tokens.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `chat-ui`: bank shell, charge states, handoff card, phone layout, white label.

## Impact

- `sentinel-ai-core/app/static/` (HTML, CSS, JS, locales), `app/routers/demo_transactions.py`, `app/schemas/chat.py`, `branding/`, tests, screenshots.

## Non-goals

- Balances, account lists, a home dashboard or any second flow.
- Model-written text.
- A separate frontend app (decision 006).
