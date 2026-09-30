# Tasks: adopt-team-branding

## 1. Brand assets and theme wiring

- [x] 1.1 Serve `branding/` from the app under a distinct static prefix and link `brand.css` plus `chat.css` in the page, owner Felix, per `branding/BRANDING.md`; verify both sheets return 200 and every existing API path still answers — evidence: `sentinel-login/tests/test_branding.py`.
- [x] 1.2 Move theme selection to `data-theme` on the document element, keeping the stored preference key unchanged, owner Felix, per `branding/brand.css`; verify light, dark, and OS-default behavior with the existing storage test intact — evidence: `sentinel-login/app/ui/static/app.js`.

## 2. Layout-only sheet

- [x] 2.1 Replace the private palette sheet with a layout-only sheet (grid, breakpoint, panel strip, receipt header placement) that references only brand variables, owner Felix, per the chosen option C; verify the desktop second column and the single-column strip below the breakpoint — evidence: `sentinel-login/app/ui/static/styles.css`.
- [x] 2.2 Add the guard test that fails on any color literal or font declaration in the local sheet, owner Felix, per the `chat-ui` spec delta; verify it fails on a planted literal and passes on the real sheet — evidence: `sentinel-login/tests/test_branding.py`.

## 3. Screens on brand classes

- [x] 3.1 Rebuild the chat view on brand classes (`.chat`, `.chat-header`, `.chat-thread`, `.msg` variants, `.candidate` chips, `.chat-input`) with the transactions panel and the receipt as a brand callout, owner Felix, per `branding/chat.css`; verify the thread, chips, receipt, and composer render in both themes — evidence: `sentinel-login/app/ui/static/index.html`.
- [x] 3.2 Bring the advisor queue and admin panel onto brand classes and table variables (`--th-bg`, `--th-text`, `--row-alt`, `--line`), owner Felix, per the `chat-ui` spec delta; verify both views follow the theme and keep their behavior — evidence: `sentinel-login/app/ui/static/app.js`.
- [x] 3.3 Audit the small-text surfaces so every label, value, and hint uses an AA text token and no status relies on color alone, owner Felix, per the contrast requirement; verify in both themes at a narrow and a wide viewport — evidence: `openspec/changes/adopt-team-branding/branding-checks.md`.

## 4. Verification

- [x] 4.1 Record the branding walkthrough (login, chat with receipt, queue, admin, light and dark, mobile and desktop, all five locales) and confirm the full suite passes, owner Felix, per the `chat-ui` spec delta; verify each row shows the brand look and no functional regression — evidence: `openspec/changes/adopt-team-branding/branding-checks.md`.
