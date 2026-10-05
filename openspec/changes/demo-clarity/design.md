---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Design

## Rules that keep the tests green

| Rule | Reason |
|---|---|
| Add elements. Do not rename or remove an id, a `data-testid` or an i18n key | `test_demo_prompts.py`, `test_ui.py` and `scripts/e2e_check.py` read them |
| Change the value of `demoHint` only | The tests check that the key exists in each locale, not its text |
| Add each new key to `es-419.json` and `pt-BR.json` | The other Spanish locales inherit from `es-419` (the `/i18n/` endpoint). `test_demo_pt_br.py` compares `pt-BR` with `es-419` |
| New elements start hidden and never block the chat form | The phone layout at 390 px must stay usable |
| Read `/health` once, without a login | The build line must not write state or need a session |
| No new request on a chat turn | The load and latency numbers stay valid |

## Decisions

| Topic | Choice | Reason |
|---|---|---|
| Where the guide lives | In the page, translated | The judge may not open the repository first |
| What the build line shows | Model, prompt version, first 8 characters of `bundle_hash`, `gold_source` | It proves that the measured build is the served build ([019](../../../docs/build/decisions/019-azure-container-apps.md)) |
| Which condition hides the examples | `demoAvailable` | The banner already uses it |
| Appearance and `bundle_hash` | Text, style and markup do not change the `bundle_hash` | Only prompt, policy, cut-offs and templates do |

## Risks

| Risk | Control |
|---|---|
| The guide text claims more than the evidence shows | The text names only the three cases and the four mocks of [what is real](../../../docs/architecture/what-is-real.md) |
| A late change breaks the phone layout | Task 4.2 repeats the captures at 390 px |
| A change after the gate | Do the work before gate G3. A later fix reopens the gate |
