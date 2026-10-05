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
- [x] 2.3 Add `.github/workflows/pages.yml` and the Pages setting note in `docs/build/delivery.md`. Evidence: the workflow and a green run after the owner enables Pages. Workflow and note written (`docs/build/delivery.md#project-site`). The green run needs the owner action. It moves to `docs-followups-2` task 7.4.

- [x] 2.4 Draw the architecture as one static SVG, `site/diagrams/architecture.svg`: the page, the session and masking, the orchestrator with the router, the policy engine, the confirm box, the tools, Gold, the case store, the advisor view, the logs and the pipeline. Colour each part as real, mock or synthetic, with a legend, as in [what is real](../../../docs/architecture/what-is-real.md). Mark where the model decides and where the code decides. This file is the single source: slide 3, the README, the video and task 4.1 reuse it. Evidence: `site/diagrams/architecture.svg` (generated, demo view, light and dark), built from `site/diagrams/architecture.json` by `scripts/build_architecture.py`.

## 3. Pitch

- [x] 3.1 Add the `## Roadmap` section to the README. Evidence: `README.md#roadmap` (six items, each with its why and a `summary.json` field or a page), `check_links.py` clean.
- [x] 3.2 Build the six slides as static HTML in `site/slides/` (1280×720, English), from the local copy of the canvas in `.local/final-push/design/`, and export them to PDF with a headless browser. The slide on limits also names the mocks and their limits, from [mocks](../../../docs/architecture/mocks.md) (moved from `evidence-hardening` 5.2). Evidence: `site/slides/` and the PDF listed in `docs/build/delivery.md`. Slide 3 ("how") shows `site/diagrams/architecture.svg` as its main picture, with the line "The AI converses. The rules decide." under it.
- [x] 3.3 Write the video script, Why → What → How, with the shot list. Evidence: `docs/build/delivery.md`. The "how" part of the script walks through `site/diagrams/architecture.svg`: the shot list names each part and the point where the code decides.

## 4. Interactive diagrams

Pages in `site/diagrams/`. Plain HTML, inline SVG and JavaScript. No library, no build. Every number comes from `site/numbers.json`. Each page works with the keyboard, at 390 px, and in light and dark mode.

- [x] 4.1 Build the architecture diagram. It shows the page, the session and masking, the orchestrator with the router, the policy engine, the confirm box, the tools, Gold, the case store, the advisor view, the logs and the Bronze, Silver and Gold pipeline. A switch changes the view between "demo" and "production". A click on a node shows its label (real, mock or synthetic), what it does, what replaces it in production and a link to the evidence. Source: [what is real](../../../docs/architecture/what-is-real.md) and [mocks](../../../docs/architecture/mocks.md). Evidence: `site/diagrams/architecture.html` and `architecture.js`, from the same source as the SVG. Tested in a browser: click, keyboard, switch, 390 px, no external request (`scripts/test_site.py`). It builds on the static SVG of task 2.4. The interactive page and the slide show the same drawing.
- [x] 4.2 Build the diagram of one chat turn. A selector gives a sample message in Spanish or Portuguese. A stepper shows the masking, the router, the policy, the lookup, the confirmation, the case opening and the read-back. Each step marks who decides (the model or the code), what goes in and out, and what can stop the turn (clarify, refuse or hand off). Evidence: `site/diagrams/turn.html`, built by `scripts/build_turn.py`: seven steps, a Spanish and a Portuguese demo line from `replay.md`, who decides, in and out, and the stops (clarify, refuse, hand off), each with its evidence file. Tested with the keyboard, at 390 px and without JavaScript.
- [x] 4.3 Build the diagram of the three demo cases on one decision map: normal, ambiguous and a person needed. Each tab lights the route to its end. The person case opens the handoff package (request, verified facts, actions, evidence, open questions). Use the case texts of `demo-clarity`. Evidence: `site/diagrams/cases.html`, built by `scripts/build_cases.py`. The demo lines come from `replay.md` and the package fields from `HandoffPackage`, both checked by a test. The page shows the fields of the package, not an invented record.
- [x] 4.4 Build the evidence explorer: a selector of metric with bars, the denominator always visible, the type label and the `summary.json` field. Include the intent accuracy of the baseline and the routers, the resolution ceiling (16 of 56 and why the difference is 0), the attack results with their counts, and cost and latency with the label of replay or live. Until the live run `2024Q4-resolution-live-v1` exists, show the replay label. The page reads `numbers.json`, so it updates when `post-freeze` task 5.1 regenerates it. Evidence: `site/diagrams/evidence.html`, built by `scripts/build_evidence.py` from the `series` of `site/numbers.json`: intent accuracy, resolution ceiling (from `resolution-gap-v1`), attacks by category, live latency, replay latency and cost.
- [x] 4.5 Cut-off diagnosis (the run `2024Q4-cutoff-diagnosis-v1` is frozen). The run holds three settings and no curve, so the page is a three-bar series of the evidence explorer and not a slider: a slider would need values that the run does not hold. Evidence: the series `cutoff` in `site/diagrams/evidence.html` (kind accuracy with no cut-offs, with the cut-off rounded to the top and with the cut-off before rounding, each on its `n`), in the three languages.
- [x] 4.6 Add tests: each diagram page loads, has no external request, is operable by keyboard, and every number matches `site/numbers.json`. Evidence: `scripts/test_site.py` (22 tests): each diagram loads, makes no external request, works with the keyboard and without JavaScript, has no horizontal scroll at 390 px, and every number matches `site/numbers.json`.

## 5. Sections for the judge

Sections of `site/index.html`, or pages in `site/`. English, ASD-STE100.

- [x] 5.1 "Try it": the link to the demo, the four cases and one sentence that the credentials are in the submission email. No password, key or bucket name. Evidence: `site/index.html#demo` (link, four cases, the credentials sentence, a test that no secret is on the site).
- [x] 5.2 "Limits and roadmap": the data limits (synthetic, Spanish only, three countries), the resolution ceiling, what was not built and why. Reuse the README `## Roadmap` of task 3.1. Evidence: `site/index.html#limits`, with the six roadmap items of the README.
- [x] 5.3 "Path to production": capacity, cost, monitoring, alerts by country and the remaining work, with links to the pages of `docs/rationale/`. Evidence: `site/judges.html#production` (nine areas, from the path to production of the specification, with the open work).
- [x] 5.4 "Reproduce": the commands to clone, run the tests and verify a frozen run offline. Evidence: `site/judges.html#reproduce`. `scripts/test_site.py` checks that `eval.run`, the run `2024Q4-train-v1`, the two environment variables, the `dev` and `eval` extras and the attack suite exist, and that every repository link resolves.
- [x] 5.5 "Screenshots": the entry page and the chat on a phone, in Spanish and Portuguese, from `scripts/capture_ui_product.py`, taken after `demo-clarity`. Evidence: `site/index.html#screens` and `site/screenshots/` (four phone screens, taken with `scripts/capture_ui_product.py` after `demo-clarity` merged). The footer of each screen shows that the demo runs the keyword baseline and the Gold mock.
- [x] 5.6 "Responsible AI": what the model never receives, results by language and country with the small-sample warning, explanations with the rule id, and the attack results. Evidence: `site/judges.html#responsible`: what the model never receives, the attack results, results by language with the small-sample warning (series `language`, with the 95% range in the evidence explorer), explanations with the rule id.
- [x] 5.7 "Team": the three owners and their areas. Evidence: `site/index.html#team`: the three names, each with a link to the GitHub profile that the repository contributors list shows (`natalia-restrepo`, `rdorta27`, `FELIX-UCHUBANDA`). Names and links only, as the owner decided.
- [x] 5.8 "Judge questions": three or four short answers (is it production, what is a mock, why is the ceiling 16 of 56). Evidence: `site/judges.html#questions` (five answers; the numbers come from `site/numbers.json`).
- [x] 5.9 Page details: title, description, preview image, favicon, a 404 page, light and dark mode, keyboard focus, and no tracking. Evidence: `site/index.html` (description, Open Graph tags, `site/preview.png`), `site/favicon.svg`, `site/404.html`, light and dark mode, focus styles, no external request, 390 px test.

The owner updates the site again after the release. The tag, the release link and the video enter then (`docs-followups-2`, group 7).

## 6. Languages and navigation

The owner asked for one navigation on every page and for the pitch in English, Spanish (Latin America, `es-419`) and Portuguese (`pt-BR`). English is the source. The Spanish and Portuguese pages are translations of it. AGENTS.md keeps the repository documents in English: this group covers `site/` only, and only because a person asked for it.

- [x] 6.1 One header, one footer and one language switch on every page (`scripts/site_chrome.py`). The current page and the current language are marked. Evidence: `test_navigation_is_the_same_on_every_page`.
- [x] 6.2 A translation tool, `scripts/localize.py`, builds `site/es-419/` and `site/pt-br/` from the English pages. A text with no translation stops the build. Numbers use the decimal comma in Portuguese. Evidence: `python3 scripts/localize.py --check`.
- [x] 6.3 The dictionaries `site/i18n/es-419.json` and `site/i18n/pt-br.json` (516 texts each). Demo lines stay in their own language. Evidence: `test_language_copies_are_current_and_complete`, `test_demo_lines_stay_in_their_own_language`.
- [x] 6.4 Tests in the three languages: same structure, links and language links resolve, no external request, no horizontal scroll at 390 px, the switch keeps the page. Evidence: `test_all_languages_in_the_browser`.
- [x] 6.6 The language follows the browser on the first visit (Spanish, Portuguese or English by default). The visitor can change it with the switch, and the choice is kept. Evidence: `site/lang.js`, `test_browser_language_is_the_default_and_the_choice_is_kept`.
- [x] 6.7 No text leaves its box in any language. `scripts/audit_overflow.py` measures HTML boxes, SVG labels, arrow labels and slides, and a test runs it. SVG labels shrink to fit their node. Evidence: `test_no_text_leaves_its_box_in_any_language`.
- [x] 6.5 One PDF of the slides for each language. Evidence: `python3 scripts/export_slides.py` writes three PDFs of six pages (gitignored).

- [x] 6.8 Name the Spanish copy with the BCP 47 tag `es-419` that `AGENTS.md` requires, and show a plain name to the reader. The switch shows «English (US)», «Español (LA)» and «Português (BR)». The folder is `site/es-419/`, the dictionary is `site/i18n/es-419.json` and the `lang` attribute is `es-419`. Evidence: `python3 scripts/localize.py --check`, the tests, and `grep -rI "es-la" .` finds nothing outside this change record.
- [x] 6.9 State in the section "Limits and roadmap" of the site and in the README `## Limitations` that the Spanish and Portuguese copies are model-written and that no native speaker reviewed them, as for the evaluation cases ([018](../../../docs/build/decisions/018-evaluation-acceptance.md)). Evidence: `site/index.html#limits` (item "Translations", in the three languages) and the README `## Limitations` (item "Site translations").
- [x] 6.10 Add to the delivery notes the commands that rebuild the copies after any change to the English text or to `site/numbers.json`: `python3 scripts/localize.py`, `python3 scripts/localize.py --check` and `python3 scripts/export_slides.py`. Evidence: `docs/build/delivery.md#project-site` (row "Rebuild the copies").

## Moved to `post-freeze`

The final numbers (old 4.1) now live in the `post-freeze` change, after the measurement and the runs. This plan closes when the site, the slides, the product page and the video script are merged.
