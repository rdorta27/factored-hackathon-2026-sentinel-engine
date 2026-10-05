---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Proposal

## Why

The organizers said that the pitch carries the most weight: slides are 60% product and 40% technical, and the video is 90% product. They also said to think like a product builder: a specific user, a specific problem and a clear difference. Today the repository has no product statement, no public site and no roadmap section. The slides of the [design canvas](https://claude.ai/artifact/U8CtkRi6b5zBLRkc5iXzuZ) are in Spanish. The evaluation is in English (REQ-0051). Three slides exist; REQ-0036 asks for 4 to 6.

## What Changes

- **Product statement:** `docs/product.md`, one page: the user, the problem with its demand data, the difference, the proof (each claim linked to the evidence index), and the tagline. Working tagline: "The AI converses. The rules decide."
- **GitHub Pages site:** a static site in `site/`, in English, from the `Pages` artboard of the canvas: the product, how it works in five steps, the measured results with their sources, the four demo cases, links to the live demo, the architecture and the repository. A workflow publishes `site/` from `main`. Every number cites a `summary.json` field.
- **Architecture drawing:** one static SVG, shared by slide 3, the README, the video and the site.
- **Interactive diagrams:** standalone pages in `site/diagrams/`: the architecture (demo and production view), one chat turn, the three demo cases, and an evidence explorer. An optional page shows why a confidence cut-off does not decide.
- **Three languages (owner request, 2026-10-05):** English, Spanish (`es-419`) and Portuguese (`pt-BR`) with one navigation. English is the source; `scripts/localize.py` builds the others. No native speaker reviews the copies, and the limits say so.
- **Judge sections:** try the demo (credentials come by email, never on the site), limits, path to production, reproduce a run, screenshots, responsible AI, team, judge questions and page details.
- **Roadmap:** a `## Roadmap` section in the README, with each item not built and its evidence (REQ-0030, REQ-0056): Customer 360, charge investigation, feedback dataset, spending assistant, policy retrieval and handoff routing.
- **Slides (six):** why (the problem and its data), what (the product and the demo), how ("The AI converses. The rules decide."), proof (results and 0 unsafe outcomes), your brand (the white label of `bank-ui`), limits and roadmap. They are static HTML pages in `site/slides/` (1280×720), exported to PDF with a headless browser. The canvas stays a visual reference.
- **Video script:** Why → What → How, with the shots from the mockups and the live demo.

## Capabilities

### New Capabilities
- `project-site`: the static site and its publication.

### Modified Capabilities
(none)

## Impact

- `docs/product.md`, `site/`, `.github/workflows/pages.yml`, `README.md`, `docs/build/delivery.md`, REQ-0013, REQ-0030, REQ-0036, REQ-0037, REQ-0051 and REQ-0056 evidence.

## Non-goals

- A site generator, a framework or an external library. Plain HTML, CSS and a little JavaScript.
- A password, key, bucket name or dataset row on the site.
- Numbers that no frozen run contains, or a time saving that we did not measure.
- Marketing claims about real banks or customers.
