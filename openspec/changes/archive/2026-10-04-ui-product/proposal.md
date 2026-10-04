# Proposal

## Why

The chat already behaves like the product (policy in code, verified cases, explained refusals, handoffs with a package), but the screens do not show it. The entry asks for a typed user and password that an evaluator does not have, the identity is a generic "SE" badge, the steps the system took are visible only in logs, and the advisor sees a plain list. The brief asks for explanations based on rules and execution records rather than model reasoning, a normal, an ambiguous and a human case, and Spanish and Portuguese (REQ-0008, REQ-0010, REQ-0011, REQ-0012, REQ-0029, REQ-0038). The design is the reviewed mockup ([canvas](https://claude.ai/artifact/U8CtkRi6b5zBLRkc5iXzuZ)), with Felix Uchubanda's review applied.

## What Changes

- **Entry:** four demo personas that sign in with one click (normal es-MX, ambiguous pt-BR on the Mexican account, high amount es-CO, "not me" es-AR), only when `SENTINEL_DEMO_AUTH=1`, under a visible demo banner; the user-and-password form stays as a secondary link. Named language buttons replace the locale code.
- **Identity:** a shield-and-eye mark and the line "Disputas de cargos no reconocidos", fonts and assets served from `branding/`, a success color distinct from the accent.
- **Chat:** a "Cómo lo resolví" panel per turn in plain language, built from translation keys the API returns with the reply; no model, tool, rule id, score or threshold is shown to the customer. Status labels keep text as well as color, and no status hints at a fraud signal before the customer acts. Suggestion chips only for flows supported end to end.
- **Advisor:** the ticket list ordered by age with reason, country and language, and a ticket detail with the handoff package and the turn trace (steps, outcome, latency, model, cost, policy version), visible only to the advisor role. The view stays read-only.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `chat-ui`: demo personas, the plain-language steps panel, the advisor trace and the brand identity.

## Impact

- `sentinel-ai-core/app/static/` (index, app.js, styles, locale files), `branding/` (mark, success color, local fonts), `app/routers/` (demo sign-in, steps in the chat reply, advisor trace route), `app/state/cases.py` (trace id on the ticket), tests.
- Not changed: the policy engine, the router, the existing fields of the reply variants.

## Non-goals

- Taking or resolving tickets from the advisor view (shown in the mockup as a proposal; the view stays read-only).
- A metrics or operations dashboard; monitoring stays in `evaluation-final`.
- Status of a case after it is opened ("¿en qué va mi caso?").

## Assumptions

- Delivered as three small PRs (entry, chat and panel, advisor) to avoid clashing with the freeze; Felix may take one.
- The chat-and-panel PR lands after `chat-loop`, whose new reply keys it renders.
