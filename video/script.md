---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Video script

The video is mandatory and lasts **3 minutes at most** (REQ-0037). This script runs **2 minutes 30 seconds**, so there is room for a slow take.

Use this page in three steps:

1. Read [Before you record](#before-you-record) once.
2. Rehearse with [Voice-over](#voice-over). It holds only the lines that you say.
3. Edit with [Shot list](#shot-list). It gives the picture and the page to open for each line.

## Before you record

### Tone

Pitch it like a product launch in front of a bank investor. The organizers weigh the video 90% on product and creativity and 10% on technique. Editing and delivery carry the most weight.

| Do | Do not |
|---|---|
| Sell the product and the need: a customer who does not recognize a charge | Present a technical project |
| Use animations, transitions and mockups, like a product launch | Record the screen and explain it |
| Use short, confident lines. One idea for each line | Read long sentences or code names |
| Show each number as proof, with its type in small text on screen | Say "production" for a simulation |
| Record the mock pages of the [Shot list](#shot-list). Use the real product only for short inserts of 3 to 5 seconds | Show a password, a key or a bucket name |

### Voice

The organizers ask for your own voice, in English. Do not use an AI voice. The panel also assesses English level, communication and narrative.

- Read the lines aloud once before you record.
- Change any line that you cannot say naturally.
- Smile on the lines with a light touch (shots 1, 5 and 8). The joke is in the words. Do not push it.
- Make a short pause at each `/` in the [Voice-over](#voice-over).

### Numbers

The numbers come from `site/numbers.json`. Run `python3 scripts/site_numbers.py` to refresh them on this page. Each number has a type. A simulation is not a production measurement. Put the type on screen next to the number.

## Timing

| Part | Shots | Time | Share of the video |
|---|---|---|---|
| 1. Why | 1 to 2 | 0:00 to 0:23 | 15% |
| 2. What | 3 to 6 | 0:23 to 1:24 | 41% |
| 3. How | 7 to 9 | 1:24 to 1:58 | 23% |
| 4. Proof and close | 10 to 11 | 1:58 to 2:30 | 21% |

## Voice-over

Read these lines aloud. The number in brackets is the shot.

### 1. Why

**[1]** It's late. / You open your bank app. / And there it is: / a charge you don't recognize.

**[2]** So you ask for help. / The chatbot makes something up. / Or an advisor makes you tell the whole story again. / In our bank data, that's <!--n~:problem_dispute_calls-->79,000+<!--/n--> calls about disputed charges.

### 2. What

**[3]** Meet Sentinel. / One conversation. / One verified case. / Or an advisor who already knows the story.

**[4]** You write in Spanish. / Sentinel finds the charge / and asks: is this the one? / You say yes. / It opens the dispute, / checks that the case really exists, / and only then gives you the number.

**[5]** Two charges that look the same? / Sentinel doesn't guess. / It asks which one. / Oh, and this customer writes in Portuguese. / No problem.

**[6]** A big amount? / Sentinel knows when to stop. / It hands the case to an advisor / with the facts already checked, / the rule that applied, / and the one question still open.

### 3. How

**[7]** So how does it work? / The AI talks. / The rules decide.

**[8]** Personal data is hidden / before the model reads a word. / The policy engine, in code, / says yes, no, or "call a human". / And every fact comes from the bank's records. / Never from the model's imagination.

**[9]** Then we tried to break it. / Prompt injections. / Broken tools. / Tricky questions in two languages.

### 4. Proof and close

**[10]** <!--n:adv_attempted-->42<!--/n--> attacks. / <!--n:adv_rate-->0/42<!--/n--> unsafe outcomes. / On turns it had never seen, / it understands <!--n:intent_router-->81.8%<!--/n-->, / against <!--n:intent_baseline-->69.2%<!--/n--> for plain keywords. / One prompt scored even higher... / but it was less safe. / So we left it out.

**[11]** Synthetic data. / Real controls. / Your brand on top, / our trust layer underneath. / Sentinel.

## Shot list

The **Page to show** column links to the page to record. Each one is a mock on the [project site](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/?lang=en), with demo data and no login. Use a mock, not the live product, unless the row asks for an insert. The link opens the right slide, tab or step.

| # | Time | Shot | Page to show | Evidence |
|---|---|---|---|---|
| 1 | 0:00 to 0:08 | Phone mockup. A charge slides in and turns red. Slow zoom on the amount. | [Slide 2, the charge card](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/slides/deck.html#2) | |
| 2 | 0:08 to 0:23 | Split screen: a wrong chatbot bubble, then an advisor with a blank form. A counter rolls up to the number. Small label: "Synthetic dataset". | [Slide 1, the size of the problem](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/slides/deck.html#1) | [`problem/dev-v1`](../evidence/problem/dev-v1/summary.json) |
| 3 | 0:23 to 0:30 | Launch title card. The logo, then the tagline "The AI talks. The rules decide." | [Slide 2, title](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/slides/deck.html#2) | |
| 4 | 0:30 to 0:52 | **Normal case.** The Spanish message, then the steps light up one by one. A 4-second insert of the chat with the case number. | [One chat turn](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/diagrams/turn.html#mask), then [the normal route](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/diagrams/cases.html#normal). Insert: [chat screenshot, es-MX](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/screenshots/chat-es-mx-phone.png) | [`replay.md`](../sentinel-ai-core/eval/demo/replay.md), case 1 |
| 5 | 0:52 to 1:06 | **Ambiguous case.** The ambiguous route lights up. The question appears in pt-BR. Nothing opens. | [The ambiguous route, in Portuguese](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/pt-br/diagrams/cases.html#ambiguous) | [`replay.md`](../sentinel-ai-core/eval/demo/replay.md), case 2 |
| 6 | 1:06 to 1:24 | **High-amount case.** The case file builds line by line: the request, the verified facts, the rule, the actions tried, the open question. | [Slide 5, the advisor case file](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/slides/deck.html#5) | [Slide 5](../site/slides/deck.html) |
| 7 | 1:24 to 1:32 | The architecture drawing assembles itself, block by block. | [Architecture](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/diagrams/architecture.html) | [`architecture-light.svg`](../site/diagrams/architecture-light.svg) |
| 8 | 1:32 to 1:50 | Three steps in turn: masking, the policy engine, the read-back. A lock icon on the model step. | [Masking](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/diagrams/turn.html#mask) → [policy](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/diagrams/turn.html#policy) → [read-back](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/diagrams/turn.html#readback) | [Architecture](../docs/architecture/README.md) |
| 9 | 1:50 to 1:58 | Attack messages hit a shield and bounce off. | [Evidence, attacks tab](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/diagrams/evidence.html#attacks) | [`adversarial`](../evidence/adversarial/20261005T014816Z/summary.json) |
| 10 | 1:58 to 2:20 | Three numbers land one after the other, each with its type ("Test suite", "Simulation"). The last line over a "Not shipped" stamp. | [Slide 4, proof](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/slides/deck.html#4), then [Evidence, intent tab](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/diagrams/evidence.html#intent) | [`eval-v8`](../evidence/evaluation-runs/2024Q4-eval-v8/summary.json), `site/numbers.json` |
| 11 | 2:20 to 2:30 | The chat in a bank brand, then the end card with the site and the repository. | [Branded chat screenshot](../docs/build/screenshots/ui-product/chat-brand-es-MX-desktop.png), then the [project site](https://rdorta27.github.io/factored-hackathon-2026-sentinel-engine/?lang=en) | [What is real](../docs/architecture/what-is-real.md) |

## Rules for the recording

- Use the mock pages and animation for the story. Use the real chat on the live link only for short inserts in shots 4 to 6.
- Show the build line of the live link only as `router_v2`, prompt `v2` and the short `bundle_hash` `2efe5962…`.
- Do not show a password, a key or a bucket name on screen.
- Put "Simulation", "Synthetic" or "Test suite" on screen next to each number. Never say "production".
- Do not claim a time saving. We did not measure one.
- Keep the demo lines from [`replay.md`](../sentinel-ai-core/eval/demo/replay.md). Do not improvise a Portuguese line.
- The system does not learn in production. If you mention the roadmap, say that the outcomes of advisor handoffs are the feedback dataset of the roadmap, not built.
- Record the inserts after the final redeploy. The live revision must match the code.
- Record with your own voice, in English. Do not use an AI voice.
- Stop at 2:30. The limit is 3:00.

## Open decisions

| Decision | Owner |
|---|---|
| The animation tool (slides with transitions, or a video editor) | Rubén |
| The recording tool (see [Pending](../docs/build/delivery.md#pending)) | Rubén |
