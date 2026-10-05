---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Video script

Mandatory video, **3 minutes at most** (REQ-0037). This script runs **2 minutes 30 seconds**, so there is room for a slow take. The judges weigh the video 90% on product and creativity and 10% on technique. The order is Why → What → How.

**Voice.** The organizers ask for your own voice, in English. Do not use an AI voice. The panel also assesses English level, communication and narrative. Read the lines aloud once before you record, and change any line that you cannot say naturally.

The numbers in this page come from `site/numbers.json`. Run `python3 scripts/site_numbers.py` to refresh them. Each number has a type: a simulation is not a production measurement. Say the type in the voice-over.

## Timing

| Part | Time | Share of the video |
|---|---|---|
| 1. Why | 0:00 to 0:25 | 17% |
| 2. What | 0:25 to 1:35 | 47% |
| 3. How | 1:35 to 2:08 | 22% |
| 4. Proof and limits | 2:08 to 2:30 | 14% |

## Shot list

| # | Time | Voice-over | Shot | Source |
|---|---|---|---|---|
| 1 | 0:00 to 0:08 | "You see a charge that you do not recognize. You open your bank app." | The phone screen of the customer with one charge. | Canvas `Mobile.dc.html` |
| 2 | 0:08 to 0:25 | "Today a chatbot may invent a fact. Or an advisor asks you everything again. In our synthetic data, <!--n:problem_dispute_calls-->79,191<!--/n--> calls are about disputes." | Two short mock-ups: a wrong answer, then an advisor with a blank form. End on the data point. | Canvas; [`problem/dev-v1`](../../evidence/problem/dev-v1/summary.json) |
| 3 | 0:25 to 0:33 | "Sentinel is the trust layer: a verified case, or a well-informed advisor." | Title card with the tagline "The AI converses. The rules decide." | Slide 2 |
| 4 | 0:33 to 0:58 | "A customer writes in Spanish. Sentinel finds the charge and asks to confirm. Only then it opens the dispute, and it reads the case back." | **Normal case.** Log in as `CUST-0001`, type the line, confirm the charge, show the case number. | [`replay.md`](../../sentinel-ai-core/eval/demo/replay.md), case 1 |
| 5 | 0:58 to 1:16 | "Two equal purchases? It does not guess. It asks which one. This customer writes in Portuguese." | **Ambiguous case.** Log in as `CUST-0002`, select `pt-BR`, type the two lines, show the candidate chips. Nothing opens. | `replay.md`, case 2 |
| 6 | 1:16 to 1:35 | "When a person must decide, the advisor gets the facts. Not a blank form." | **Human case.** Use the high-amount case: it hands off with no insistence. Log in as `CUST-0003`, ask for an advisor, then open the advisor view. Show the ticket list (reason, country, language, age). Then show the detail: the request, the verified facts, the actions that the system tried, the evidence with the rule id, the open questions and the trace of the turn. | `replay.md`, case 3; canvas `Advisor.dc.html` |
| 7 | 1:35 to 1:45 | "How does it work? The model only labels the intent. Everything else is code." | The architecture drawing. Start with the whole picture. | `site/diagrams/architecture-light.svg` |
| 8 | 1:45 to 2:00 | "The code masks personal data before the model. The policy engine allows, refuses or hands off. The code, not the model, writes each fact." | Zoom on the masking, the router (the only pink part), the policy engine and the confirm box. Mark where the code decides. | Same drawing; [architecture](../architecture/README.md) |
| 9 | 2:00 to 2:08 | "We attacked it. A prompt injection does not change a decision." | One injection attempt in the chat that the system refuses. | [`adversarial`](../../evidence/adversarial/20261005T014816Z/summary.json) |
| 10 | 2:08 to 2:22 | "<!--n:adv_attempted-->42<!--/n--> attacks in the test suite. <!--n:adv_rate-->0/42<!--/n--> unsafe outcomes. The router reads the intent with <!--n:intent_router-->98.2%<!--/n--> accuracy against <!--n:intent_baseline-->53.9%<!--/n--> for the keyword baseline. Those two are simulations." | Slide 4. | `site/numbers.json` |
| 11 | 2:22 to 2:30 | "The data is synthetic and some parts are mocks. We say which. The system does not learn in production: the outcomes of advisor handoffs are the feedback dataset of our roadmap, not built. Your brand, our trust layer." | Slide 6, then the brand slide. End card with the repository and the live demo. | Slides 5 and 6; [what is real](../architecture/what-is-real.md) |

## Rules for the recording

- Show the real chat on the live link for shots 4 to 6. Do not show a password or a bucket name.
- Show the build line of the live link only as `router_v2`, prompt `v2` and the short `bundle_hash` `2efe5962…`. Do not show a password, a key or a bucket name on screen.
- Say "simulation" or "test suite" next to each number. Never say "production".
- Do not claim a time saving. We did not measure one.
- Keep the demo lines from [`replay.md`](../../sentinel-ai-core/eval/demo/replay.md). Do not improvise a Portuguese line.
- Record after the final redeploy. The live revision must match the code.
- Record with your own voice, in English. Do not use an AI voice.
- Keep each line short. Stop at 2:30. The limit is 3:00.

## Open decisions

| Decision | Owner |
|---|---|
| Screen capture only, or capture with animation | Rubén |
| The recording tool (see [Pending](delivery.md#pending)) | Rubén |
