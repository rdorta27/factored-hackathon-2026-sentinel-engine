---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# Design

## Decisions

1. **The canvas is the visual source.** Colors, type and layout come from the canvas artboards `Main`, `Chat`, `Mobile` and `Advisor`, mapped to the tokens in `branding/`. The UI text stays in es-419 and pt-BR.
2. **Case state comes from the server.** The page never computes eligibility. The server joins the session charges with the case store and the policy result.
3. **White label is configuration.** Two variables at startup. The accent goes through the contrast check of `chat-ui` ("Contrast-safe text tokens"). An accent that fails falls back to the default and logs it.
4. **Masked product only.** The header shows the product type and the last four digits. No balance, no full number, no name.
5. **Phone first for the thread.** Below 700 px the side panels become a drawer. Touch targets are at least 44 px.

## Risks

- The page changes while `flow-fixes` and `chat-start` change the replies. Mitigation: the page reads reply kinds and keys, not text.
- Screenshots go stale. Mitigation: regenerate them in the last task.

## Coordination with `flow-fixes` (2026-10-04)

6. **Merge `flow-fixes` first.** It edits `app/schemas/chat.py` (optional fields), the locale files and, if needed, one line of `static/app.js`. This change owns the HTML, CSS and JavaScript and rebases on that commit.
7. **Reuse the reply kinds that exist.** The page already renders the `explanation` kind with `fillTemplate` and verified values. New states and the handoff card use the same pattern. Do not add a second way to fill placeholders.
8. **Use the same state names.** `case_state` values match the `case_status` values that `flow-fixes` returns for a dispute status reply, so the panel and the reply agree.
9. **The design is a local copy.** Read `.local/final-push/design/` (README with tokens); the original canvas is not readable from every tool. Run `uvicorn` on port 8003.
