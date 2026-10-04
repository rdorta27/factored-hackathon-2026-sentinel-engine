---
language: en
style: ASD-STE100
last_reviewed: 2026-10-04
---

# 006 · Frontend: one-page chat served by FastAPI

**Date:** 2026-09-28
**Status:** Accepted
**Participants:** Rubén Dorta

Closes pending decision 11.

## Context

The demo is a chat with a test login, a thread, candidate charges and an explicit confirmation before a dispute opens. It must be clear in a 3-minute video. Felix owns the full-stack build.

## Options

1. **Streamlit or Gradio.** Fast to start, and known for data work. They look like a notebook. The session, the confirmation and an audit log are difficult in them.
2. **A one-page chat served by FastAPI** (HTML and a little JavaScript, same process). Login, thread, candidates, confirm button.
3. **A separate Node app.** Permitted, and better for the video, but a second app to deploy on Thursday.

## Decision

A one-page chat served by FastAPI. Streamlit and Gradio are out. Node only if Felix asks for it to improve the video.

## Consequences

- *Updated 9/29:* a confirm box confirms each action that changes state (`.chat-confirm` in `branding/chat.css`). The page sends the candidate id to `POST /chat` as a structured field, not as text ([confirmation](../../architecture/specification.md#confirmation)).
- No second framework and no second process for the deploy on Thursday.
- The page sends the message and the session to `POST /chat`. It never sends a customer id for the tools to trust.
