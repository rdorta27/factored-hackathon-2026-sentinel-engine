# Design

## Context

See proposal.md for why. No `sentinel-ai-core/` package exists. The loop contracts live in `docs/architecture/specification.md`. Decision 005 fixes Python and FastAPI and defers the loop tool. This change does not add a route.

## Goals / Non-Goals

**Goals:**

- A turn function tests can call without HTTP.
- Policy as a pure function over facts already gathered.
- Session-bound tool ports, with in-memory fakes.
- A fake model port scripted per demo case.

**Non-Goals:**

- Choosing a graph library. Plain Python is the skeleton.
- Serving `POST /chat` or storing the session.
- Implementing the real classifier or measuring the category list.

## Decisions

### Plain Python state, not a graph

The pause between the confirm box and the button is another turn input, not a model message. An explicit state object (turns, candidates shown, pending confirmation, language, clarification count) is enough. Alternative rejected: LangGraph in-process. It would hide the same state in a checkpoint and add a dependency the skeleton does not need (decision 005).

### Tools are bound before the turn

The caller constructs tool ports already scoped to the session. `step` does not take `customer_id`. That keeps decision 005 (the loop never sees `customer_id`) and still lets tools filter by the session. Alternative rejected: passing `customer_id` into the turn so the loop can inject it. That puts the identifier where a prompt can leak it.

### Token authorizes the turn, key authorizes the retry

`confirmation_token` is minted when the structured candidate id matches the pending confirmation, passed once into the open-dispute port, and never shown to the model. The idempotency key is `session + candidate + action`. Read-back retries reuse that key and do not mint a new token. The open-dispute port returns the existing record when the key is already used, so a single-use token and a retry do not conflict. Alternative rejected: a fresh token per attempt. The second attempt would fail as already used.

### Three attempts is a skeleton constant

The specification says retries are bounded and does not set the count. This change uses three attempts total (the first call plus two retries) and logs the attempt number. The constant lives next to the loop, not in country policy files. Alternative rejected: unbounded retry until the read-back succeeds.

### Fake model is a script, not a keyword policy

`understand(message, turns)` returns intent, language (`es-419` or `pt-BR`), and charge hints, or that a detail is missing. `classify(message)` returns a category and is called only after policy allows the dispute. Tests assert outcome kind, not wording. A duplicate charge is the normal case with a different category, not a fourth demo case. Alternative rejected: keyword routing inside the loop as the decision maker. That would make the fake model the policy.

### Types follow the specification nouns

Four shapes: a candidate charge (opaque id, status, amount, currency, merchant, date, as-of date), conversation state, turn input (text or candidate id), and turn output (question, confirm box, case number, handoff, or failure). The token is a value, not a fifth shape. Names that are not in the specification (`Intent`, `ToolResult`, `PolicyOutcome`) are not introduced as public types.

## Risks / Trade-offs

- [Risk] Three attempts and the token lifetime are not in the specification → Mitigation: document both as skeleton assumptions; token is valid only for the confirmation turn, clock injected in tests.
- [Risk] The architecture page says the loop injects `customer_id`, decision 005 says it never sees it → Mitigation: binding happens at the tool port, before `step`. The page's "injects" is satisfied by calling a bound port.
- [Risk] Category list is unmeasured (decision 007) → Mitigation: the category port returns a string; tests supply the expected category. No enum of subcategories in this change.
- [Risk] Callers do not exist yet → Mitigation: tests call `step` directly. The HTTP harness is a later change.

## Migration Plan

1. Add the package and tests on this branch.
2. Rollback is deleting `sentinel-ai-core/` from the branch. Nothing in `main` calls it.

## Open Questions

- None that change the specs or the task split. Token TTL stays "the confirmation turn" until a caller exists to expire it sooner.
