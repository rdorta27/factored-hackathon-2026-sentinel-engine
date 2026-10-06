---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Video script

The video is mandatory and lasts **3 minutes at most** (REQ-0037). This script runs **2 minutes 30 seconds**, so there is room for a slow take.

Use this page in two steps:

1. Read [Before you record](#before-you-record) once.
2. Record and edit with the [Shot list](#shot-list). Each row gives the line that you say, the picture and the mockup to record.

## Before you record

### Tone

Pitch it like a product launch in front of a bank investor. The organizers weigh the video 90% on product and creativity and 10% on technique. Editing and delivery carry the most weight.

| Do | Do not |
|---|---|
| Sell the product and the need: a customer who does not recognize a charge | Present a technical project |
| Use animations, transitions and mockups, like a product launch | Record the screen and explain it |
| Use short, confident lines. One idea for each line | Read long sentences or code names |
| Show each number as proof, with its type in small text on screen | Say "production" for a simulation |
| Record the [mockups](mockups/) of the [Shot list](#shot-list). Use the real product only for short inserts of 3 to 5 seconds | Show a password, a key or a bucket name |

### Voice

The organizers ask for your own voice, in English. Do not use an AI voice. The panel also assesses English level, communication and narrative.

- Read the lines aloud once before you record.
- Change any line that you cannot say naturally.
- Smile on the lines with a light touch (shots 1, 5 and 8). The joke is in the words. Do not push it.
- Make a short pause at each `/` in the voice-over.

### Numbers

The voice-over says each number in words. This table links each spoken number to its value in `site/numbers.json`. Run `python3 scripts/site_numbers.py` to refresh the values. If a value changes, change the words and mockups 2 and 10 too.

| Shot | You say | Value | Type on screen |
|---|---|---|---|
| 2 | "seventy-nine thousand" | <!--n~:problem_dispute_calls-->79,000+<!--/n--> | Synthetic |
| 10 | "forty-two" | <!--n:adv_attempted-->42<!--/n--> | Test suite |
| 10 | "zero" | <!--n:adv_rate-->0/42<!--/n--> | Test suite |
| 10 | "almost eighty-two percent" | <!--n:intent_router-->81.8%<!--/n--> | Simulation |
| 10 | "about sixty-nine percent" | <!--n:intent_baseline-->69.2%<!--/n--> | Simulation |

A simulation is not a production measurement. Put the type on screen next to the number.

## Timing

| Part | Shots | Time | Share of the video |
|---|---|---|---|
| 1. Why | 1 to 2 | 0:00 to 0:23 | 15% |
| 2. What | 3 to 6 | 0:23 to 1:24 | 41% |
| 3. How | 7 to 9 | 1:24 to 1:58 | 23% |
| 4. Proof and close | 10 to 11 | 1:58 to 2:30 | 21% |

## Shot list

Each **Mockup** link opens an animated HTML page at 1920×1080. The animation plays when the page opens.

| Key | Action |
|---|---|
| `F` | Full screen |
| `R` or a click | Play again |
| `H` | Hide the key hint before you record |

Mockups of Sentinel copy the look and the texts of the real app. "Other app" mockups show a fictitious bank, Banco Nimbus, with a different look. The data is demo data.

| # | Time | Voice-over | Shot | Mockup |
|---|---|---|---|---|
| 1 | 0:00 to 0:08 | "It's late. / You open your bank app. / And there it is: / a charge you don't know." | **Other app.** A fictitious bank app. The Cafe Central charge slides in, turns red, and the camera zooms in. | [01-charge.html](mockups/01-charge.html) |
| 2 | 0:08 to 0:23 | "So you ask for help. / The chatbot makes something up. / Or an agent asks you to start again. / In our bank data, / that's seventy-nine thousand calls / about charges like this." | **Other app.** Split screen: a chatbot that invents a refund and a case number, then an advisor with a blank form. Both blur, and a counter rolls up. Label: "Synthetic dataset". | [02-problem.html](mockups/02-problem.html) |
| 3 | 0:23 to 0:30 | "Meet Sentinel. / One chat. / One verified case. / Or an advisor who already knows the story." | **Launch card.** The Sentinel mark, the name, the three promises and the tagline. | [03-meet.html](mockups/03-meet.html) |
| 4 | 0:30 to 0:52 | "You write in Spanish. / Sentinel finds the charge / and asks: is this the one? / You say yes. / It opens the case, / checks that it's really there, / and only then gives you the number." | **Sentinel, normal case (es-MX).** The message types in. The steps light up. The confirm box appears, the button is tapped, and the verified receipt appears. | [04-normal.html](mockups/04-normal.html) |
| 5 | 0:52 to 1:06 | "Lots of charges that look alike? / Sentinel doesn't guess. / It asks which one. / Oh, and this customer writes in Portuguese. / No problem." | **Sentinel, ambiguous case (pt-BR).** The question and the candidate charges appear. A note says that no case is open. | [05-ambiguous.html](mockups/05-ambiguous.html) |
| 6 | 1:06 to 1:24 | "A big amount? / Sentinel knows when to stop. / It sends the case to an agent, / with the facts already checked, / the rule that applied, / and the one question left." | **Sentinel, high amount.** The chat hands off. The advisor view opens, and the case file builds line by line. | [06-handoff.html](mockups/06-handoff.html) |
| 7 | 1:24 to 1:32 | "So how does it work? / The AI talks. / The rules decide." | **Architecture.** Eight blocks pop in. One is the model. The others are code and a person. | [07-architecture.html](mockups/07-architecture.html) |
| 8 | 1:32 to 1:50 | "First, we hide personal data / before the model sees a word. / Then the rules, in plain code, / say yes, no, or "call a human". / Every fact comes from the bank. / Never from the model's imagination." | **Three controls.** A name and a card turn into `[NAME]` and `[CARD]`. The rules check and "Allow" lights up. The case is opened, then read back. | [08-controls.html](mockups/08-controls.html) |
| 9 | 1:50 to 1:58 | "Then we tried to break it. / Tricks. / Broken tools. / Hard questions in two languages." | **Attacks.** Attack messages in English, Spanish and Portuguese hit the Sentinel shield and bounce off. | [09-attacks.html](mockups/09-attacks.html) |
| 10 | 1:58 to 2:20 | "Forty-two attacks. / Zero unsafe outcomes. / On chats it had never seen, / it gets almost eighty-two percent right. / Simple keywords get about sixty-nine. / One newer version scored even higher... / but it was less safe. / So we left it out." | **Proof.** The two attack numbers land with "Test suite". The bars grow with "Simulation". The v3 bar gets a "Not shipped" stamp. | [10-proof.html](mockups/10-proof.html) |
| 11 | 2:20 to 2:30 | "Test data. / Real controls. / Your brand on top. / Our trust layer underneath. / Sentinel Engine." | **Close.** The same chat in three fictitious bank brands, then the end card: the mark, **Sentinel Engine**, the tagline and the site. | [11-close.html](mockups/11-close.html) |

## Rules for the recording

- Use the mockups for the story. Use the real chat on the live link only for short inserts in shots 4 to 6.
- Open each mockup in Chromium or Chrome, press `F` and `H`, then record the screen at 1920×1080. Press `R` to play the shot again.
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
