---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Reference

This folder holds official hackathon material. The team keeps it in the repository because members need the column-level detail at hand. It is the one exception to the rule that the official material stays out of the repository. The problem statement, the kickoff and the dataset summary stay as the personal copy of each member.

| File | What it is |
|---|---|
| [latam-bank-data-dictionary.md](latam-bank-data-dictionary.md) | The LATAM Bank v1.0.0 data dictionary: 13 tables, columns, types, constraints and foreign keys |

## Rules

- **This is source material, not our writing.** Do not edit the content to reflect our design. Keep it as the official reference.
- **Formatting only.** The original is a PDF export with broken tables. The team reformatted the tables to clean Markdown. The content is verbatim. A split inside a word in the original (for example `Cre|dit Card`) is rejoined.
- **Cite it. Do not fork it.** For the synthesis of the team, read [dataset.md](../dataset.md). For the machine contract, see [`sentinel-data-engine/catalog.py`](../../../sentinel-data-engine/src/sentinel_data/catalog.py) and [`schemas.py`](../../../sentinel-data-engine/src/sentinel_data/schemas.py).

**Provenance:** LATAM Bank Dataset Version 1.0.0, generated in July 2026 for the Factored Datathon 2026. It is fully synthetic.
