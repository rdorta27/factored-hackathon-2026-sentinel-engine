# 006 · Frontend: one-page chat served by FastAPI

**Date:** 2026-09-28
**Status:** Accepted
**Participants:** Rubén Dorta

Closes pending decision 11.

## Context

The demo is a chat with a test login, a thread, candidate charges and an explicit confirmation before opening a dispute. It has to read clearly in a 3-minute video. Felix owns the full-stack build.

## Options

1. **Streamlit or Gradio.** Fast to stand up, and familiar for data work. They look like a notebook, and session, confirmation and an audit log are awkward.
2. **A one-page chat served by FastAPI** (HTML and a little JavaScript, same process). Login, thread, candidates, confirm button.
3. **A separate Node app.** Allowed, and finer for the video, but a second app to deploy on Thursday.

## Decision

A one-page chat served by FastAPI. Streamlit and Gradio are out. Node only if Felix asks for it to polish the video.

## Consequences

- *Updated 9/29:* state-changing actions are confirmed with a confirm box (`.chat-confirm` in `branding/chat.css`); the page sends the candidate id to `POST /chat` as a structured field, not as text ([confirmation](../../architecture/specification.md#confirmation)).

- No second framework and no second process for the Thursday deploy.
- The page talks to `POST /chat` with the message and the session. It never sends a customer id for the tools to trust.
