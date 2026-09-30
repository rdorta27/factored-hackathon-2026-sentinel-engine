# Reference

Official hackathon material kept in the repository because the team needs the
column-level detail at hand. It is the one exception to the rule that the
official material stays out of the repository; the problem statement, the
kickoff, and the dataset summary are still each member's own copy.

| File | What it is |
|---|---|
| [latam-bank-data-dictionary.md](latam-bank-data-dictionary.md) | LATAM Bank v1.0.0 data dictionary: 13 tables, columns, types, constraints, and foreign keys. |

## Rules

- **This is source material, not our writing.** Do not edit the content to
  reflect our design; keep it as the official reference.
- **Formatting only.** The original is a PDF export with broken tables. The
  tables here were reformatted to clean Markdown and the content is verbatim.
  A mid-word split in the original (for example `Cre|dit Card`) was rejoined.
- **Cite it, do not fork it.** For the team's synthesis read
  [dataset.md](../dataset.md); for the machine contract see
  [`sentinel-data-engine/catalog.py`](../../../sentinel-data-engine/src/sentinel_data/catalog.py)
  and [`schemas.py`](../../../sentinel-data-engine/src/sentinel_data/schemas.py).

**Provenance:** LATAM Bank Dataset Version 1.0.0, generated July 2026 for the
Factored Datathon 2026. Fully synthetic.
