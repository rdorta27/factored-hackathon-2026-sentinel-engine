---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Decisions: [018](../../../docs/build/decisions/018-evaluation-acceptance.md), [019](../../../docs/build/decisions/019-azure-container-apps.md). Design: [canvas](https://claude.ai/artifact/U8CtkRi6b5zBLRkc5iXzuZ). Paths are relative to the repository root.

## 1. Product

- [ ] 1.1 Write `docs/product.md`: user, problem with demand data, difference, proof and tagline. Evidence: the page, with every claim linked to the evidence index.

## 2. Site

- [ ] 2.1 Build `site/` in English from the `Pages` artboard. Evidence: `site/index.html` at desktop and phone width.
- [ ] 2.2 Add `scripts/site_numbers.py` and a test that the page numbers match the evidence. Evidence: `site/numbers.json` and the test.
- [ ] 2.3 Add `.github/workflows/pages.yml` and the Pages setting note in `docs/build/delivery.md`. Evidence: the workflow and a green run after the owner enables Pages.

## 3. Pitch

- [ ] 3.1 Add the `## Roadmap` section to the README. Evidence: README, REQ-0030 evidence.
- [ ] 3.2 Translate the three canvas slides to English and add the problem, results and limits slides. Evidence: the canvas link and its export in `docs/build/delivery.md`.
- [ ] 3.3 Write the video script, Why → What → How, with the shot list. Evidence: `docs/build/delivery.md`.

## 4. Final numbers

- [ ] 4.1 After `eval-v8` and the robustness runs, regenerate `site/numbers.json` and update the slides. Evidence: the test of 2.2 passes.
