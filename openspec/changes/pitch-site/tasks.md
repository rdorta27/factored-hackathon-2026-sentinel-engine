---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Tasks

Decisions: [018](../../../docs/build/decisions/018-evaluation-acceptance.md), [019](../../../docs/build/decisions/019-azure-container-apps.md). Design: [canvas](https://claude.ai/artifact/U8CtkRi6b5zBLRkc5iXzuZ). Paths are relative to the repository root.

## Order of work and cut

Work in this order. Merge each step before the next. If time runs out, cut from the bottom. The core list must be merged first.

| Step | Tasks | Why |
|---|---|---|
| 1. Base | 2.1, 2.2, 2.3, 2.4 | The site, the numbers script, the Pages workflow and the static architecture drawing. Slide 3 and the video need the drawing |
| 2. Pitch | 1.1, 3.2, 3.3, 3.1 | Product page, slides, video script and roadmap. The organizers weigh them most |
| 3. Core of the site | 4.1, 4.3, 4.4, 4.6, 5.1, 5.2, 5.9 | The architecture, the three cases, the evidence, the tests, how to try it, the limits and the page details |
| 4. Next | 4.2, 5.3, 5.4, 5.5, 5.6 | One chat turn, path to production, reproduce, screenshots, responsible AI |
| 5. Optional | 4.5, 5.7, 5.8 | Cut-off slider, team, judge questions |

The site is updated again after the release (`docs-followups-2`, group 7).

## 1. Product

- [x] 1.1 Write `docs/product.md`: user, problem with demand data, difference, proof and tagline. Evidence: `docs/product.md`, every claim linked to its `summary.json` field. `scripts/test_site.py` checks its four problem numbers against the evidence.

## 2. Site

- [x] 2.1 Build `site/` in English from the `Pages` artboard. Evidence: `site/index.html` (hero, five steps, results, four cases, links), `site/style.css`, `site/404.html`, checked at 1280 px and 390 px in light and dark mode.
- [x] 2.2 Add `scripts/site_numbers.py` and a test that the page numbers match the evidence. Evidence: `site/numbers.json` (15 numbers) and `scripts/test_site.py` (7 tests). The script writes the text of each `data-num` slot, so no number is typed by hand.
- [ ] 2.3 Add `.github/workflows/pages.yml` and the Pages setting note in `docs/build/delivery.md`. Evidence: the workflow and a green run after the owner enables Pages. Workflow and note written (`docs/build/delivery.md#project-site`). The green run needs the owner action. It moves to `docs-followups-2` task 7.4.

- [x] 2.4 Draw the architecture as one static SVG, `site/diagrams/architecture.svg`: the page, the session and masking, the orchestrator with the router, the policy engine, the confirm box, the tools, Gold, the case store, the advisor view, the logs and the pipeline. Colour each part as real, mock or synthetic, with a legend, as in [what is real](../../../docs/architecture/what-is-real.md). Mark where the model decides and where the code decides. This file is the single source: slide 3, the README, the video and task 4.1 reuse it. Evidence: `site/diagrams/architecture.svg` (generated, demo view, light and dark), built from `site/diagrams/architecture.json` by `scripts/build_architecture.py`.

## 3. Pitch

- [ ] 3.1 Add the `## Roadmap` section to the README. Evidence: README, REQ-0030 evidence.
- [ ] 3.2 Build the six slides as static HTML in `site/slides/` (1280×720, English), from the local copy of the canvas in `.local/final-push/design/`, and export them to PDF with a headless browser. The slide on limits also names the mocks and their limits, from [mocks](../../../docs/architecture/mocks.md) (moved from `evidence-hardening` 5.2). Evidence: `site/slides/` and the PDF listed in `docs/build/delivery.md`. Slide 3 ("how") shows `site/diagrams/architecture.svg` as its main picture, with the line "The AI converses. The rules decide." under it.
- [ ] 3.3 Write the video script, Why → What → How, with the shot list. Evidence: `docs/build/delivery.md`. The "how" part of the script walks through `site/diagrams/architecture.svg`: the shot list names each part and the point where the code decides.

## 4. Interactive diagrams

Pages in `site/diagrams/`. Plain HTML, inline SVG and JavaScript. No library, no build. Every number comes from `site/numbers.json`. Each page works with the keyboard, at 390 px, and in light and dark mode.

- [x] 4.1 Build the architecture diagram. It shows the page, the session and masking, the orchestrator with the router, the policy engine, the confirm box, the tools, Gold, the case store, the advisor view, the logs and the Bronze, Silver and Gold pipeline. A switch changes the view between "demo" and "production". A click on a node shows its label (real, mock or synthetic), what it does, what replaces it in production and a link to the evidence. Source: [what is real](../../../docs/architecture/what-is-real.md) and [mocks](../../../docs/architecture/mocks.md). Evidence: `site/diagrams/architecture.html` and `architecture.js`, from the same source as the SVG. Tested in a browser: click, keyboard, switch, 390 px, no external request (`scripts/test_site.py`). It builds on the static SVG of task 2.4. The interactive page and the slide show the same drawing.
- [ ] 4.2 Build the diagram of one chat turn. A selector gives a sample message in Spanish or Portuguese. A stepper shows the masking, the router, the policy, the lookup, the confirmation, the case opening and the read-back. Each step marks who decides (the model or the code), what goes in and out, and what can stop the turn (clarify, refuse or hand off). Evidence: `site/diagrams/turn.html`.
- [ ] 4.3 Build the diagram of the three demo cases on one decision map: normal, ambiguous and a person needed. Each tab lights the route to its end. The person case opens the handoff package (request, verified facts, actions, evidence, open questions). Use the case texts of `demo-clarity`. Evidence: `site/diagrams/cases.html`.
- [ ] 4.4 Build the evidence explorer: a selector of metric with bars, the denominator always visible, the type label and the `summary.json` field. Include the intent accuracy of the baseline and the routers, the resolution ceiling (16 of 56 and why the difference is 0), the attack results with their counts, and cost and latency with the label of replay or live. Until the live run `2024Q4-resolution-live-v1` exists, show the replay label. The page reads `numbers.json`, so it updates when `post-freeze` task 5.1 regenerates it. Evidence: `site/diagrams/evidence.html`.
- [ ] 4.5 (optional, only if the run `2024Q4-cutoff-diagnosis-v1` is frozen) Build the slider "when to act": move the confidence cut-off and see the share of turns that act and the kind accuracy. Evidence: `site/diagrams/cutoff.html`.
- [ ] 4.6 Add tests: each diagram page loads, has no external request, is operable by keyboard, and every number matches `site/numbers.json`. Evidence: the tests.

## 5. Sections for the judge

Sections of `site/index.html`, or pages in `site/`. English, ASD-STE100.

- [ ] 5.1 "Try it": the link to the demo, the four cases and one sentence that the credentials are in the submission email. No password, key or bucket name. Evidence: the section.
- [ ] 5.2 "Limits and roadmap": the data limits (synthetic, Spanish only, three countries), the resolution ceiling, what was not built and why. Reuse the README `## Roadmap` of task 3.1. Evidence: the section and its links.
- [ ] 5.3 "Path to production": capacity, cost, monitoring, alerts by country and the remaining work, with links to the pages of `docs/rationale/`. Evidence: the section.
- [ ] 5.4 "Reproduce": the commands to clone, run the tests and verify a frozen run offline. Evidence: the section and a check that each command exists.
- [ ] 5.5 "Screenshots": the entry page and the chat on a phone, in Spanish and Portuguese, from `scripts/capture_ui_product.py`, taken after `demo-clarity`. Evidence: the images in `site/`.
- [ ] 5.6 "Responsible AI": what the model never receives, results by language and country with the small-sample warning, explanations with the rule id, and the attack results. Evidence: the section and its links.
- [ ] 5.7 "Team": the three owners and their areas. Evidence: the section.
- [ ] 5.8 "Judge questions": three or four short answers (is it production, what is a mock, why is the ceiling 16 of 56). Evidence: the section.
- [ ] 5.9 Page details: title, description, preview image, favicon, a 404 page, light and dark mode, keyboard focus, and no tracking. Evidence: `site/` and a check at 390 px.

The owner updates the site again after the release. The tag, the release link and the video enter then (`docs-followups-2`, group 7).

## Moved to `post-freeze`

The final numbers (old 4.1) now live in the `post-freeze` change, after the measurement and the runs. This plan closes when the site, the slides, the product page and the video script are merged.
