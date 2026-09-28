# Flow evidence, third run (Q4-2024, 2026-09-28, 70/30 cut)

Adds univariate separation audits to the second run in
[`../2024Q4-v2/`](../2024Q4-v2/README.md); the first run in [`../`](../README.md)
stays frozen. Data is shared: this script reads `evidence/flows/data/`.

**Caveat:** the `*_learnable: false` flags are fixed in code and come from
one-field-at-a-time rates. They show no univariate signal; they do not rule
out a multivariate model, which still has to be compared against a baseline
on a time split (REQ-0016).

Deterministic record of the flow measurements behind the Tuesday 9/29 flow
review. `summary.json` is the output of `measure_flow.py summary` (script
`2026-09-28+q4-7030-v3`, held-out cut 2025-07-01) over the data in `MANIFEST.md`.
v2 added: `reception_channel = Regulator` share, `was_escalated` on window
calls (not per complaint — linkage is 0%), open-vs-terminal fill audit for
REQ-0017, and the `reason_category` degeneracy finding (no CNR-like call
subcategory). v3 added: univariate learnability audits for all four targets
(all flat → `*_learnable: false`; code + verification, no learned components).

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
transaction-related contact reason; *Comercial* = sales;
*Producto* = product; *Queja* = complaint; *Retención* = retention;
*Técnico* = technical; *Préstamo Personal* = personal loan;
*Préstamo Hipotecario* = mortgage.

## Reproduce

```bash
python3 measure_flow.py verify   # must match MANIFEST.md, all lines
python3 measure_flow.py summary  # regenerates summary.json
```

See `method.md` before touching any date. Never download data at/after
2025-07-01 before the single final held-out measurement.
