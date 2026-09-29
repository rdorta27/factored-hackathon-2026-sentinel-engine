# Sentinel Engine branding

Source of truth for slides, docs and the one-page chat (decision 006).
Palette: violet `#6d4aff` + rose `#ff4f8b` on warm white, with a dark variant.
Typography: Newsreader (titles) + Source Sans 3 (body) + Source Code Pro (mono).

## Files

| File | Use |
|---|---|
| `brand.css` | Variables only. `:root` is light, `[data-theme="dark"]` is dark. Import first. |
| `theme-sentinel.css` | Gradient details, focus rings, cards. Used by slides/docs on top of `estilos/base.css`. |
| `chat.css` | Chat thread, candidates, confirm box, input. Used by the FastAPI one-page chat. |
| `preview.html` | Static preview, no build step. Open directly in a browser. |

## Usage

Slides/docs (local PDF pipeline):

```html
<link rel="stylesheet" href="../repo-hackathon/branding/brand.css">
<link rel="stylesheet" href="base.css">
<link rel="stylesheet" href="../repo-hackathon/branding/theme-sentinel.css">
```

Chat (FastAPI serves `branding/` as static files):

```html
<link rel="stylesheet" href="/static/branding/brand.css">
<link rel="stylesheet" href="/static/branding/chat.css">
```

Dark mode: set `data-theme="dark"` on `<html>`. Light: `data-theme="light"` or no attribute.
Print/PDF always renders light.

## Rules

- No pandoc, chromium or any build step required for this folder. Those are local-only
  tools of `~/Work/factored/estilos/build.py` and never a repo dependency.
- `~/Work/factored/estilos/` is a loose copy for internal PDFs. It may diverge;
  no sync is enforced. Seed it once by copying `brand.css` and `theme-sentinel.css`
  over `theme-newsreader.css` if needed.
- Never commit PDFs, `.env` or datasets. See `AGENTS.md`.
