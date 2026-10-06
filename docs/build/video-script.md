---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Video script

The video is mandatory and lasts **3 minutes at most** (REQ-0037). This script runs **2 minutes 30 seconds**, so there is room for a slow take.

## Tone

Pitch it like a product launch in front of a bank investor. The organizers weigh the video 90% on product and creativity and 10% on technique. Editing and delivery carry the most weight.

| Do | Do not |
|---|---|
| Sell the product and the need: a customer who does not recognize a charge | Present a technical project |
| Use animations, transitions and mockups, like a product launch | Record the screen and explain it |
| Use short, confident lines. One idea for each line | Read long sentences or code names |
| Show each number as proof, with its type in small text on screen | Say "production" for a simulation |
| Show the real product in short inserts of 3 to 5 seconds | Show a password, a key or a bucket name |

**Voice.** The organizers ask for your own voice, in English. Do not use an AI voice. The panel also assesses English level, communication and narrative. Read the lines aloud once before you record. Change any line that you cannot say naturally.

**Numbers.** The numbers on this page come from `site/numbers.json`. Run `python3 scripts/site_numbers.py` to refresh them. Each number has a type. A simulation is not a production measurement. Put the type on screen next to the number.

## Timing

| Part | Time | Share of the video |
|---|---|---|
| 1. Why | 0:00 to 0:25 | 17% |
| 2. What | 0:25 to 1:35 | 47% |
| 3. How | 1:35 to 2:08 | 22% |
| 4. Proof and close | 2:08 to 2:30 | 14% |

## Shot list

| # | Time | Voice-over | Shot | Source |
|---|---|---|---|---|
| 1 | 0:00 to 0:08 | "You open your bank app. There is a charge you don't recognize." | Animated phone mockup. A charge slides in and turns red. Slow zoom on the amount. | Slide 1, the mockup of slide 2 |
| 2 | 0:08 to 0:25 | "Today, a chatbot might invent an answer. Or an advisor asks you everything again. In our bank data, that's more than <!--n~:problem_dispute_calls-->79,000+<!--/n--> calls about disputed charges." | Split screen: a chatbot bubble that is wrong, then an advisor with a blank form. The counter rolls up to the number. Small label: "Synthetic dataset". | [`problem/dev-v1`](../../evidence/problem/dev-v1/summary.json) |
| 3 | 0:25 to 0:33 | "Meet Sentinel. A verified case in one conversation, or an advisor who already has the facts." | Launch title card. The logo, then the tagline "The AI talks. The rules decide." | Slide 2 |
| 4 | 0:33 to 0:58 | "You write in Spanish. Sentinel finds the charge and asks you to confirm. Only then does it open the dispute. And it checks that the case exists before it gives you the number." | **Normal case.** Phone mockup with the chat bubbles animated, then a 4-second insert of the real chat with the case number. | [`replay.md`](../../sentinel-ai-core/eval/demo/replay.md), case 1 |
| 5 | 0:58 to 1:16 | "Two charges that look the same? It doesn't guess. It asks which one. And this customer writes in Portuguese." | **Ambiguous case.** Two identical charge cards slide in side by side. The question bubble appears in pt-BR. Nothing opens. | `replay.md`, case 2 |
| 6 | 1:16 to 1:35 | "A large amount? Sentinel does not act alone. It hands the case to an advisor, with the facts already checked, the rule that applied and the open question." | **High-amount case.** The chat hands off with no insistence. Cut to the advisor view: the ticket list (reason, country, language, age), then the case file builds line by line: the request, the verified facts, the actions tried, the rule id, the open question. | `replay.md`, case 3; slide 5 |
| 7 | 1:35 to 1:45 | "How does it work? The AI talks. The rules decide." | The architecture drawing assembles itself, block by block. | `site/diagrams/architecture-light.svg` |
| 8 | 1:45 to 2:00 | "Personal data is masked before the model sees anything. The policy engine, in code, allows, refuses or hands off. And every fact comes from the bank's data, not from the model." | Zoom on three blocks in turn: masking, the policy engine, the read-back. A lock icon on the model block. | Same drawing; [architecture](../architecture/README.md) |
| 9 | 2:00 to 2:08 | "We attacked it. A prompt injection does not change a decision." | One injection message hits a shield and bounces off. | [`adversarial`](../../evidence/adversarial/20261005T014816Z/summary.json) |
| 10 | 2:08 to 2:22 | "<!--n:adv_attempted-->42<!--/n--> attacks: <!--n:adv_rate-->0/42<!--/n--> unsafe outcomes. It understands <!--n:intent_router-->81.8%<!--/n--> of the sealed test turns, against <!--n:intent_baseline-->69.2%<!--/n--> for keywords. And a newer prompt scored higher, but it was less safe. So we didn't ship it." | Three numbers land one after the other, each with its small type label ("Test suite", "Simulation"). The last line over a "Not shipped" stamp. | Slide 4; `site/numbers.json` |
| 11 | 2:22 to 2:30 | "Synthetic data, real controls. Your brand, our trust layer. Sentinel." | The same chat in two bank brands, then the end card with the repository and the site. | Slides 5 and 6; [what is real](../architecture/what-is-real.md) |

## Rules for the recording

- Use mockups and animation for the story. Use the real chat on the live link only for short inserts in shots 4 to 6.
- Show the build line of the live link only as `router_v2`, prompt `v2` and the short `bundle_hash` `2efe5962…`. Do not show a password, a key or a bucket name on screen.
- Put "Simulation", "Synthetic" or "Test suite" on screen next to each number. Never say "production".
- Do not claim a time saving. We did not measure one.
- Keep the demo lines from [`replay.md`](../../sentinel-ai-core/eval/demo/replay.md). Do not improvise a Portuguese line.
- The system does not learn in production. If you mention the roadmap, say that the outcomes of advisor handoffs are the feedback dataset of the roadmap, not built.
- Record after the final redeploy. The live revision must match the code.
- Record with your own voice, in English. Do not use an AI voice.
- Keep each line short. Stop at 2:30. The limit is 3:00.

## Open decisions

| Decision | Owner |
|---|---|
| The animation tool (slides with transitions, or a video editor) | Rubén |
| The recording tool (see [Pending](delivery.md#pending)) | Rubén |
