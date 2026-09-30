# Proposal: adopt-team-branding

## Why

The interface works but does not look like the team's product: `branding/` landed on `main` as the single source of truth for slides, docs, and the one-page chat, and the app still ships a private palette and typography. The screens a reviewer sees must match the brand deck, or the demo reads as two different products.

## What Changes

- Serve `branding/brand.css` and `branding/chat.css` in the app and set the theme with `data-theme` on `<html>`, so light/dark come from the brand variables only.
- Adopt option C from the design exploration: brand `chat.css` as the chat foundation plus one small local sheet limited to **layout and positioning**. Color, typography, and spacing SHALL come from brand variables; a test fails if the local sheet introduces a color literal or a font family.
- Desktop (>= 1000px): chat thread in the brand column with the transactions panel as a second column that reuses `.candidate` vertically. Below that, a single column with the panel as a horizontal strip above the thread.
- Verified receipt card: brand `.msg-audit` container with a minimal header (accent check plus the word for verified, case id in `--font-mono`) and the five elements as label/value rows.
- Advisor queue: one `.msg-audit` card per case with `.candidate` buttons to claim and advance. Admin panel: brand table variables (`--th-bg`, `--row-alt`, `--line`).
- Contrast compliance: AA-passing tokens (`--text`, `--title`) for body text; `--muted` limited to large or non-essential text and to borders/backgrounds, because it does not meet AA for small text on light backgrounds.
- Retire the private palette: `app/ui/static/styles.css` becomes the layout-only sheet, and the brand preview file stays as a standalone reference.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `chat-ui`: adds the brand adoption requirements (brand tokens as the only source of color and type, layout-only local sheet, brand-class receipt and queue surfaces, and the contrast rule). Existing behavior requirements stay untouched.

## Impact

- Code: `sentinel-login/app/ui/` (markup, the layout sheet, and the static mount for `branding/`). No backend, contract, or endpoint change.
- Assets: `branding/` is read as-is and never modified; served from the app without a build step.
- Tests: the 150 existing tests stay green. New tests pin the brand stylesheet links, the absence of color/font literals in the local sheet, the layout-only rule, and the AA token rule.
- Traces to REQ-0038 (P0), REQ-0041 (P0), REQ-0051 (P0); builds on `docs/build/decisions/006-frontend.md` and `branding/BRANDING.md`.

## Non-goals

- No change to `branding/` itself, no build step, no fonts beyond what the brand sheet imports.
- No functional change: IDs, endpoints, reply contracts, i18n keys, and the theme-preference storage key stay as they are.
- No mobile app, no new screens, no dashboard beyond the existing admin panel.
