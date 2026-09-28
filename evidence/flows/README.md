# Flow evidence (Q4-2024, frozen 2026-09-28, 70/30 cut)

Deterministic record of the flow measurements behind the Tuesday 9/29 flow
review. `summary.json` is the output of `measure_flow.py summary` (script
`2026-09-28+q4-7030`, held-out cut 2025-07-01) over the data in `MANIFEST.md`.

| File | What it is |
|---|---|
| `measure_flow.py` | Exact script used (stdlib only) |
| `summary.json` | The evidence: metrics + CIs + script version + window. **Cite this, never hand-transcribed numbers.** |
| `MANIFEST.md` | Methodology + data hashes (`verify` reference) |
| `method.md` | Window, cut and date convention (event dates, held-out 2025-07 → 2026-06) |

## Immutability rule

This folder is write-once: never edit after freezing. A new run gets a new
dated folder under `evidence/flows/`; a file here is replaced only with the
reason recorded in the commit message.

## How to cite

Reference `summary.json` fields directly (e.g. `disputes.unrecognized_claim`,
`accounts.reason_transaccional`). Per-mode stdout logs (`run_*.log`) stay local
and are not committed. Raw data (`data/`, ~200 MB) is never committed.

Spanish values are dataset values, kept as-is: *Cargo no reconocido* =
unrecognized charge; *Tarjeta Crédito* = credit card; *Transaccional* =
transaction-related contact reason.

## Reproduce

```bash
python3 measure_flow.py verify   # must match MANIFEST.md, all lines
python3 measure_flow.py summary  # regenerates summary.json
```

See `method.md` before touching any date. Never download data at/after
2025-07-01 before the single final held-out measurement.
