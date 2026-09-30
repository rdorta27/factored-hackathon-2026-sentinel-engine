# Design: adopt-team-branding

## Context

See proposal.md (Why). Option C from the design exploration is the chosen
approach: brand `chat.css` as the chat foundation plus one small local sheet
limited to layout. Current state: `app/ui/static/styles.css` defines a private
palette and typography (its own `:root` tokens, system-ui stack, semantic
colors), and `app/ui/static/index.html` links only that sheet. `branding/` is on
`main` and must not be touched.

Constraints that shaped the decisions below, verified by reading the brand files:

| Finding | Consequence |
|---|---|
| `--ok` is `#6d4aff`, the same violet as `--accent`; there is no green | "Verified" cannot be a green badge; it is accent + an explicit word |
| `--muted` (`#a09cb5`) is roughly 2.5:1 on `--bg` in light mode | Muted is for borders, fills, and large text only; body text uses `--text` |
| `brand.css` imports Google Fonts by URL | Offline falls back to `Georgia`/`system-ui`, already declared in the variables |
| `chat.css` is chat-only (thread, candidates, confirm, input) | Login, queue, and admin need composition from brand variables, not new brand classes |

## Goals / Non-Goals

**Goals:**

- One visual language across slides, docs, and the app, with `branding/` as the
  only source of color and type.
- Keep the shipped CSS surface small enough to review in one sitting.

**Non-Goals:**

- Not adopting the type scale from `brand.css` for slides (`--fs-h2`,
  `--fs-card`, and similar are print-oriented and would dwarf a chat UI).
- No markup framework, no build step, no change to functional IDs or contracts.

## Decisions

- **Serve `branding/` from the app instead of copying it.** The brand folder is
  mounted as static files and linked from the page, so the app cannot drift from
  the source of truth. Copying would create a second copy that silently goes
  stale; the cost is one static mount and a path that must match the mount.
  Alternative rejected: vendoring the CSS into `app/ui/`.
- **Two brand links plus one local sheet.** `brand.css` then `chat.css`, both
  from the brand folder, then `layout.css` for structure only. `chat.css` already
  assumes `brand.css` variables, so the order is forced. Alternative rejected: a
  single merged sheet, which would hide which rule came from where.
- **Layout-only local sheet, enforced by test.** The sheet adds the grid, the
  breakpoint, and the panel strip behavior. A test scans it for color literals
  and font declarations and fails on either, which is the only thing preventing a
  second design system growing back. Alternative rejected: relying on review.
- **Receipt as a brand callout with a minimal own header.** The card uses
  `.msg-audit` for the container (brand left accent border, callout background)
  and adds only a header row: accent check plus a word, case id in `--font-mono`.
  Using brand classes keeps the theme inheritance free. Alternative rejected: a
  bespoke card, which would need its own colors and break the inheritance.
- **Contrast by token choice, not by new colors.** Body text uses `--text`;
  titles use `--title`; `--muted` is restricted to hints at larger size, borders,
  and fills. No new color is introduced, so the palette stays identical to the
  deck. Alternative rejected: darkening `--muted`, which would mean editing the
  brand folder.
- **`--ok` for verified, with the word always present.** Since `--ok` equals the
  accent, the check plus the label carries the meaning and the color is
  reinforcement. This satisfies "never color alone" without inventing green.
  Alternative rejected: hardcoding a green, which would sit outside the brand.
- **Table variables for the admin panel.** `--th-bg`, `--th-text`, `--row-alt`,
  and `--line` give the admin view the same table look the docs use, so the
  fourth screen is not visually orphaned.
- **Keep `data-theme` and the stored preference key.** The brand sheet already
  keys dark mode off `data-theme`, and `app.js` already writes only the theme
  preference, so both sides meet without a storage change.

## Risks / Trade-offs

- [Risk] A brand update changes a variable and shifts the app's look → Mitigation:
  that is the intended behavior of a single source of truth; the brand sheet is
  the place to fix it, not the app.
- [Risk] `--muted` used on small text fails AA → Mitigation: a test asserts the
  local sheet does not assign `--muted` to text, and every small label uses a
  text token.
- [Risk] The local sheet drifts into styling → Mitigation: the color/font test,
  plus keeping it under a screenful of rules.
- [Risk] Google Fonts unreachable offline → Mitigation: the fallbacks declared in
  `brand.css` render the app; noted as a brand-folder property, not fixed here.
- [Risk] The static mount path for `branding/` could collide with API routes →
  Mitigation: mount under a distinct prefix and assert the existing API paths
  still answer in the suite.

## Migration Plan

1. Serve `branding/` and link the two brand sheets; the app renders in brand
   colors with the current layout.
2. Replace the private sheet with the layout-only sheet; screens adopt brand
   classes for chat, receipt, queue, and admin.
3. Verify both themes, the five locales, the breakpoint, and the full suite.
4. Rollback: restore the previous sheet and links; no data or contract change.

## Open Questions

- None that change specs or tasks. Whether to vendor `branding/` into the
  deployment artifact is a deploy concern and stays with the deploy change.
