# Tasks

Areas: [ai](../../../docs/build/areas/ai.md). Decisions: [006](../../../docs/build/decisions/006-frontend.md), [009](../../../docs/build/decisions/009-demo-ui-and-advisor-view.md), [017](../../../docs/build/decisions/017-portuguese.md). Mockup: [canvas](https://claude.ai/artifact/U8CtkRi6b5zBLRkc5iXzuZ). Paths are under `sentinel-ai-core/` unless stated. Keep existing ids, add `data-testid`, `textContent` only, every string in both locales.

## 1. Entry (PR 1)

- [x] 1.1 Mark (inline SVG), purpose line, success color in `branding/brand.css`, woff2 fonts with `@font-face` in `branding/`. Evidence: `tests/test_branding.py` extended (no external font URL, success token exists).
- [x] 1.2 Demo sign-in route behind `SENTINEL_DEMO_AUTH`, four personas, demo banner, named language buttons, password form as a secondary link; README limitation. Evidence: tests for 404 without the flag and a session per persona; `tests/test_ui.py` for the banner.

## 2. Chat and panel (PR 2, after chat-loop)

- [x] 2.1 Map each turn's records to the closed step keys and add `steps` to the reply. Evidence: `tests/test_contract.py` (strict field) and tests per outcome kind that no rule id, model or threshold appears.
- [x] 2.2 Render the "Cómo lo resolví" panel and neutral status labels; show chips only for supported flows. Evidence: `tests/test_ui.py` and `tests/test_demo_prompts.py`.

## 3. Advisor (PR 3)

- [x] 3.1 Store the escalating turn's `trace_id` on the ticket and add the advisor-only trace route. Evidence: `tests/test_handoffs_api.py` (customer refused, steps listed, no text or identifier).
- [x] 3.2 Ticket list by age with reason, country and language, and the detail with package and trace; read-only. Evidence: `tests/test_ui.py` and a manual run recorded in `team/chat-manual-tests.md`.

## 4. Close

- [ ] 4.1 Screenshots of the four screens in es-MX and pt-BR, desktop and phone width, compared with the mockup; update README and REQ-0038 evidence. Evidence: notes in `team/chat-manual-tests.md` and those files.
