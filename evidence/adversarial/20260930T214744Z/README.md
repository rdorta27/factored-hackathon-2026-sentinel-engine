# Adversarial run 2026-09-30

Frozen evidence for the adversarial set (REQ-0021, REQ-0007, REQ-0047). This
folder is write-once: never edit `summary.json`; a new run gets a new dated
folder under `evidence/adversarial/`.

## How it was produced

From `sentinel-ai-core/`:

```bash
SENTINEL_WRITE_EVIDENCE=1 python -m pytest tests/adversarial -q
```

The counts in `summary.json` are derived from the real pytest outcomes by the
hooks in `tests/adversarial/conftest.py`, never hand-maintained. The run
result was `28 passed, 4 xfailed`.

## What it says

Cite `summary.json` fields, never hand-transcribed numbers.

- `totals.unsafe_outcome_rate` is `unsafe_outcomes/attempted`, where the
  denominator is **every attack attempted** and `unsafe_outcomes` counts
  failures among the attacks that expect a defence (`blocked_verified` +
  `passes_on_mock`). Here it is `0/29`.
- `no_defense_yet` attacks are `xfail(strict=True)` and are **not** counted as
  defences; `documented` (B4) is a known limitation asserted on purpose.
- `attacks` lists every attack with its group, node id and real outcome.

| Group | Meaning |
|---|---|
| `blocked_verified` | a defence exists in production code |
| `passes_on_mock` | safe only because the model is the stand-in `app/ai/demo.py:DemoModel`, not a real LLM |
| `no_defense_yet` | no control yet; `xfail(strict=True)` names the pending decision |
| `documented` | asserts a known limitation (bearer-cookie replay) |

`covered_elsewhere` lists attacks already covered by `test_chat.py`,
`test_transactions.py` and `test_confirmation.py`; they are listed for the
report, never re-implemented here.
