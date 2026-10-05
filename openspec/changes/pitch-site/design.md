---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **Plain static files.** `site/index.html`, one CSS file, inline SVG icons, no build step. GitHub Pages serves them as they are.
2. **Numbers from evidence only.** A small script (`scripts/site_numbers.py`) reads the frozen `summary.json` fields and writes `site/numbers.json`. The page reads it. A test fails if a number on the page differs from the evidence.
3. **Labels stay visible.** Each number on the site shows its type from [what is real](../../../docs/architecture/what-is-real.md): simulation, test suite or projection.
4. **Canvas is the design source.** Colors and type follow the canvas and `branding/`. The site text is English and in ASD-STE100.
5. **Publication by workflow.** `.github/workflows/pages.yml` uploads `site/` with `actions/upload-pages-artifact` and deploys it with `actions/deploy-pages`, on pushes to `main` that change `site/`.

8. **Diagrams are standalone pages.** Each page in `site/diagrams/` works alone and the main page links it. They use inline SVG and plain JavaScript, no library. They work with the keyboard, at 390 px and in light and dark mode.
9. **Diagram numbers come from `numbers.json`.** No number is typed in a diagram. The numbers test covers them. Each bar shows its denominator and its type (simulation, test suite or projection).
10. **No secret on the site.** The "Try it" section tells the visitor that the credentials are in the submission email. The site holds no password, key, bucket name or dataset row.
11. **The site is refreshed twice.** Once before the release, with the frozen numbers (`post-freeze` 5.1). Once after the release, with the tag, the release link and the video (`docs-followups-2` group 7).

## Risks

- Repository Pages settings need an owner action. Mitigation: the task lists the one setting to change.
- Numbers change after `eval-v8`. Mitigation: regenerate `site/numbers.json` in the last task.

## Tools (2026-10-04)

6. **Slides do not need claude.ai.** The canvas can be read only through Claude. The slides live in the repository as static pages, so Claude Code and OpenCode can both edit them, and GitHub Pages can also serve them.
7. **Design source.** Read `.local/final-push/design/` (HTML copy and README with tokens), not the canvas link.
