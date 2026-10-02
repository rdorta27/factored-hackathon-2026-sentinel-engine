# Rationale

Why the system is built the way it is, written for the people who evaluate it. Each page explains one choice so it can go straight into the [presentation](../build/delivery.md#presentation) and the [video](../build/delivery.md#video-pitch).

This folder is not a decision log. [Decisions](../build/decisions/) record *what* was chosen; these pages explain *why*, what was rejected, what changes in production, and the line that goes on a slide.

## Pages

| Page | The choice in one line | Slide |
|---|---|---|
| [Data assumptions](data-assumptions.md) | Accounts exist only in México, Colombia and Argentina; currency belongs to the product, not the country | 1, 5 |
| [Policy thresholds](policy-thresholds.md) | Fraud and high-amount handoffs use synthetic per-currency values a bank replaces without code | 3 |
| [Policy sources](policy-sources.md) | The dispute policy is synthetic: what the customer sees of it, its known defects and where real values come from | 3 |
| [Router model selection](router-model-selection.md) | Open-weight models chosen per route by a rule fixed before measuring | 2, 4 |
| [What the model never receives](model-data-minimization.md) | The model gets the customer's words only; ids, personal data and the fraud score stay in code | 3 |
| [One app, state outside the process](one-app-state-outside.md) | One FastAPI app and one API; sessions, conversation and cases survive a restart | 2 |
| [What the public link runs](public-link.md) | The deployed demo runs the measured router with a baseline fallback and the labeled Gold mock, and says so | 5 |
| [Repository history](repository-history.md) | An old commit names the data bucket; we did not rewrite history, and why | 5 |

## How to write a page

Each page has the same parts:

1. **Choice:** one sentence.
2. **Why:** the evidence or constraint behind it, with links.
3. **Alternatives rejected:** and why.
4. **In production:** what would change.
5. **On the slide:** the sentence we say.

Numbers are never typed by hand: they cite a frozen `summary.json` field.
