# Branding checks: adopt-team-branding

Verified 2026-09-29 with `pytest -q` (**165 passed**) on Python 3.12.10, plus a
`/ui/` walkthrough. Option C is implemented: brand `chat.css` as the chat
foundation, one local sheet for layout only.

## Brand assets

| Check | Result |
|---|---|
| `/branding/brand.css` and `/branding/chat.css` | 200, served read-only from the repo root |
| `branding/` modified | No — the folder is untouched |
| Local sheets in `app/ui/static/` | Exactly one (`styles.css`); the old palette file was replaced, not kept |
| Old palette gone | No `--color-primary`, no `system-ui` in the local sheet |
| API routes after the brand mount | `/docs`, `/i18n/*`, `/auth/*`, `/chat`, `/api/v1/*` all still answer |

## Layout-only lock (the tests that enforce it)

| Rule | Test |
|---|---|
| No hex/rgb/hsl color value | `test_local_sheet_has_no_color_literal` |
| No named colors in a value position | `test_local_sheet_has_no_named_colors` |
| No `font-size` / `font-weight` | `test_local_sheet_declares_no_font_size_or_weight` |
| Exactly one font rule, from a brand variable | `test_local_sheet_uses_mono_only_through_a_brand_variable` |
| Color-valued properties reference a brand variable | `test_local_sheet_only_colors_through_brand_variables` |
| Verified color configurable in one line | `test_verified_color_is_configurable_in_one_place` |

Violations found and fixed while writing these tests (all in the app's own sheet,
none in `branding/`):

1. Two `font-weight: 700` declarations leaked typography into the layout sheet.
2. `border-radius: 999px` matched the color-property rule because of a
   substring match on `border`; the rule was narrowed to real color properties
   and the radius changed to `12px` to match the brand's card radius.
3. The verified color was declared once and referenced once, but the first
   version of the rule counted the comment too; the check now strips comments.

## Contrast tokens

| Surface | Token | Note |
|---|---|---|
| Body text, labels, values | `--text` / `--title` | AA against their backgrounds in both themes |
| Hints and secondary lines | `chat-sub` (brand class) | brand sheet sizes and colors it; no small muted text in the local sheet |
| Verified state | `--app-verified` → `--ok`, plus the word | color reinforces, the check and the word carry the meaning |
| Borders and fills | `--line`, `--callout-bg`, `--th-bg`, `--row-alt` | never load-bearing for meaning |

## Functional regression

| Check | Result |
|---|---|
| `view-login`, `thread`, `transactions` ids | present and unchanged |
| Reply kinds, i18n keys, storage key | unchanged |
| Theme storage | still only the theme preference |

## Browser checklist

Serve one process and open `http://127.0.0.1:8000/ui/`:

**Desktop (>= 1000px)**

1. Login as `CUST-0001` / `Testpass-001`: two columns, chat left, transactions
   right, sticky-looking panel.
2. Type a wrong-date dispute: clarification with candidate chips, in brand
   pill style.
3. Tap a transaction in the right panel: the bubble describes it, the receipt
   appears as a brand callout with the check, the word "Verificado", and the
   case number in mono.
4. Toggle dark: every surface flips, including the panel and the receipt.
5. Switch to `pt-BR` in the header selector: header, chips, receipt all change.

**Mobile (narrow the window below 1000px)**

6. The transactions panel moves above the chat and becomes a horizontal strip.
7. Chips and the receipt stay usable; the case number still fits.

**Advisor and admin**

8. Log out, sign in as `ADV-0001` / `Advisor-001`: queue cards in brand callout
   style with a pill button to claim.
9. Sign in as `ADM-0001` / `Admin-001`: metrics table uses the brand table
   variables in both themes.

**Both themes, all four screens** — nothing should keep a color from the old
palette (no blue-grey); everything should read as violet/rose on warm white, or
its dark counterpart.
