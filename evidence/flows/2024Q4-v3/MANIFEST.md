# Data manifest — Q4-2024 working window + snapshots

Generated 2026-09-28, re-verified after the P1–P6 remediation. All files local
under `evidence/flows/data/` (shared with the first run, gitignored), synced
from the datathon S3 bucket. The bucket name is read from `BUCKET` in `.env`
and is never written in the repository. Run the hash snippet from
`evidence/flows/`. Prefer `python3 measure_flow.py verify` over the snippet
below — same check, no copy-paste.

Reproduce hashes with:
```bash
python3 -c "
import csv, glob, hashlib
for pat in ['data/complaints/year=2024/month=10/day=*/*.csv',
            'data/complaints/year=2024/month=11/day=*/*.csv',
            'data/complaints/year=2024/month=12/day=*/*.csv',
            'data/windows/2024Q4/interactions/day=*/*.csv',
            'data/windows/2024Q4/transactions/day=*/*.csv',
            'data/windows/2024Q4/transcripts/*/*/*.csv',
            'data/snapshots/products.csv',
            'data/snapshots/customers.csv']:
    fs = sorted(glob.glob(pat)); n = 0; h = hashlib.sha256()
    for f in fs:
        h.update(open(f, 'rb').read())
        n += sum(1 for _ in csv.DictReader(open(f, newline='', encoding='utf-8-sig')))
    print(f'{len(fs):4d} files | {n:7d} rows | {h.hexdigest()[:16]} | {pat}')
"
```

| Files | Rows | sha256[:16] | Pattern |
|---|---|---|---|
| 31 | 1,877 | f44525712f4aaa69 | data/complaints/year=2024/month=10/day=*/*.csv |
| 30 | 1,872 | dd0226d7e9eded5a | data/complaints/year=2024/month=11/day=*/*.csv |
| 31 | 1,885 | d5bc0fda797c788b | data/complaints/year=2024/month=12/day=*/*.csv |
| 92 | 56,045+235* | ee67115957357e09 | data/windows/2024Q4/interactions/day=*/*.csv |
| 92 | 370,659+1,277* | 161dad7a76971923 | data/windows/2024Q4/transactions/day=*/*.csv |
| 92 | 14,023 | 8d1406ac172a0321 | data/windows/2024Q4/transcripts/*/*/*.csv |
| 1 | 400,000 | f071906b4342b35f | data/snapshots/products.csv |
| 1 | 150,000 | c5bb1f835d688b61 | data/snapshots/customers.csv |

\* Partition totals; the script filters to event dates in [2024-10-01,
2025-01-01), excluding 235 calls + 1,277 transactions + 23 complaints dated
2025-01-01 (late arrivals by design: partitions are `process_date`).
`complaints/` on disk also holds year=2023 and year=2025 (full history,
56,763 rows total) — declared, hashed on demand, never scanned by any mode
(`COMPLAINT_PATS` is built from WINDOW).

Snapshot date spread (`last_updated` year → rows):
- products: 2018: 7,232 · 2019–2025: ~50k each · **2026: 42,575 · 2027: 5,344**
  → filter `last_updated < 2025-07-01` keeps 327,035, excludes 72,965.
- customers: 2019–2025: ~18.7k each · **2026: 15,861 · 2027: 1,999**;
  `registration_date >= 2026`: 8,517. `customers.csv` is stored but **no mode
  reads it** (reserved for a future sizing check; contains synthetic PII —
  never to the repo or an LLM).

Cleaning for every scanned row: utf-8-sig, strip, drop fully-empty
(0 dropped everywhere). If S3 contents change, hashes will differ — re-sync
and re-run all four modes.
