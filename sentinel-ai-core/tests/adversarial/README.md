# Adversarial set

Failure tests for REQ-0021, REQ-0007 and REQ-0047: bad or missing data, expired
session, unauthorized access, prompt injection, tool failure and multilingual
ambiguity, in Spanish and Portuguese.

Run from `sentinel-ai-core/`:

    python -m pytest tests/adversarial -q

Write one evidence run (opt-in; a normal test run never touches the repo):

    SENTINEL_WRITE_EVIDENCE=1 python -m pytest tests/adversarial -q

## Honesty groups

Every attack test carries `@pytest.mark.attack("<id>", "<group>")`:

| Group | Meaning |
|---|---|
| `blocked_verified` | a defence exists in production code |
| `passes_on_mock` | safe only because the live model is the keyword stand-in `app/ai/demo.py:DemoModel`, not a real LLM (decision 10) |
| `no_defense_yet` | no control yet; `xfail(strict=True)` names the pending decision that unblocks it |
| `documented` | asserts a known design limitation on purpose (B4 bearer-cookie replay) |

`tests/adversarial/summary.py` derives the report from the real pytest outcomes
via hooks in `conftest.py`. No count is hand-maintained: if an attack that
expects a defence fails, `unsafe_outcomes` moves. The denominator is every
attack attempted. A missing mark fails collection.

`covered_elsewhere` in `summary.py` lists attacks already covered by
`test_chat.py`, `test_transactions.py` and `test_confirmation.py`; they are
listed for the report, never duplicated here.
