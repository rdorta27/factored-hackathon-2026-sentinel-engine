---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [006](../../../docs/build/decisions/006-frontend.md), [008](../../../docs/build/decisions/008-account-inquiry-scope.md), [009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md). Design: [canvas](https://claude.ai/artifact/U8CtkRi6b5zBLRkc5iXzuZ). Paths are under `sentinel-ai-core/` unless stated.

## 1. API

- [x] 1.1 Add `case_state` per charge to `GET /api/v1/transactions`. Evidence: `tests/test_transactions.py` for each state, and no new personal field (`tests/adversarial/`).

## 2. Page

- [x] 2.1 Add the bank shell with the masked product and the as-of date. Evidence: `tests/test_ui.py`.
- [x] 2.2 Show the charge states in the recent-charges panel. Evidence: tests and screenshots.
- [x] 2.3 Show the handoff card in the thread. Evidence: tests.
- [x] 2.4 Make the layout work on a phone (390 px) with the drawer. Evidence: phone screenshots.
- [x] 2.5 Add `SENTINEL_BRAND_NAME` and `SENTINEL_BRAND_ACCENT` with the contrast fallback. Evidence: tests and one screenshot with another brand.

## 3. Review

- [ ] 3.0 Human review G1 of the look and the four persona journeys; apply the changes. Evidence: notes in `team/chat-manual-tests.md`.

## 4. Evidence

- [ ] 4.1 Regenerate the screenshots and update REQ-0038 evidence and the demo architecture. Evidence: `docs/build/screenshots/ui-product/`, `docs/requirements/frontend-backend.md`.
