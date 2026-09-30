# Regression checks: fix-chat-grounding-and-locale

Verified 2026-09-29 with `pytest -q` (**129 passed**) on Python 3.12.10, plus a
live walkthrough against one `uvicorn` process on `/ui/` and `/docs`.

## Reported bugs

| Bug | Reproduction | Before | Now | Test |
|---|---|---|---|---|
| Case opened on a transaction the customer never described | `I dispute the charge of 1000.00 at ACME Store on 2026-09-20` | case opened on `TXN-1001` (2026-06-10) | `clarification` + 6 candidates, **0 cases created** | `test_chat.py::test_wrong_date_never_opens_a_case` |
| 90-day window silently wrong | `TXN-1002` (2026-01-15) treated as eligible | eligible | refused, reason names the window and the day count | `test_eligibility.py::test_stale_row_refused` |
| Currency tied to language | — | no per-country customers | MX/COP/ARS each read their own currency, locale only formats | `test_customer_api.py::test_each_country_lists_its_own_currency` |
| Raw keys and ISO dates on screen | card rendered `hold`, `rule`, `ref` + `2026-06-21T00:00:00+00:00` | raw | every card string translated, dates via `Intl.DateTimeFormat` | `test_i18n.py::test_no_raw_keys_or_iso_dates_in_render_code` |
| Amount hold implied money movement | `temporarily held (simulated)` | claimed a hold | `no_funds_held` statement, `hold` field gone | `test_disputes.py::test_eligible_creates_case_with_proof` |
| `/` not usable | `GET /` | 404 | 307 to `/ui/` | `test_i18n.py::test_root_redirects_to_ui` |

## Grounding matrix

| Statement | Outcome | Cases | Test |
|---|---|---|---|
| exact date + amount + merchant | `matched` | 1 | `test_grounding.py::test_exact_match_selects_one` |
| amount + merchant, two dates | `ambiguous` (both offered) | 0 | `test_same_amount_two_dates_is_ambiguous` |
| wrong date | `none` | 0 | `test_wrong_date_matches_nothing` |
| contradictory merchant | `none` | 0 | `test_contradictory_merchant_matches_nothing` |
| Spanish, `1.000,00`, month name | `matched` | 1 | `test_grounding_locales.py::test_spanish_message_grounds_to_the_charge` |
| Portuguese, `R$ 1.000,00`, month name | `matched` | 1 | `test_portuguese_message_grounds_to_the_charge` |
| Portuguese, two charges, no date | `ambiguous` | 0 | `test_portuguese_ambiguous_message_clarifies` |

## Window boundaries (reference date 2026-06-17)

| Age | Result | Test |
|---|---|---|
| 89 days | eligible | `test_day_89_is_inside_the_window` |
| 90 days | eligible | `test_day_90_is_inside_the_window` |
| 91 days | refused, "91 days" in the reason | `test_day_91_is_outside_the_window` |

## Live walkthrough

| Step | Observed |
|---|---|
| `GET /` | 307 → `/ui/` |
| Login `CUST-0001` | chat view, transactions panel loaded, reference date shown |
| Wrong-date dispute | `clarification` with candidate chips, no case |
| Exact dispute | `case_confirmation`, `CASE-0001`, `no_funds_held` present, no `hold` field, `display.currency = MXN`, `display.referenceDate = 2026-06-17` |
| Stale dispute | `handoff` |
| Login `CUST-0002` / `CUST-0003` | COP / ARS transactions, default locale `es-CO` / `es-AR` |
| `/docs` and `/auth/login` | reachable (200 / 200) |

## Note on the local UI file

`app/ui/static/index.html` had been replaced locally by a branding preview. It
was preserved as `app/ui/static/brand-preview.html` and the application markup
restored from git before this walkthrough. Two tests now pin real app ids
(`view-login`, `thread`, `transactions`) and the `app.js` / `styles.css`
references, so a future overwrite fails the suite instead of passing by luck.
