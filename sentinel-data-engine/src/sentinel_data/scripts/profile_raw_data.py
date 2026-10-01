"""
Raw data profiling script for Sentinel Engine Silver layer quality audit.

Connects to DuckDB, registers all 13 raw tables as views, and audits data quality
across six dimensions:
  1. Categorical & text standardisation
  2. Completeness & null patterns
  3. Primary key uniqueness & duplication
  4. Referential integrity
  5. Temporal & numerical range sanity
  6. PII field inventory

Run from the sentinel-data-engine directory:
    python profile_raw_data.py [--raw-dir data/raw/data] [--out data_quality_report.md]
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Table registry
# ---------------------------------------------------------------------------

# Tables delivered as a single flat CSV.
_FLAT_TABLES: dict[str, str] = {
    "customers": "customers.csv",
    "products": "products.csv",
    "service_agents": "service_agents.csv",
    "branches": "branches.csv",
    "daily_exchange_rates": "daily_exchange_rates.csv",
    "marketing_campaigns": "marketing_campaigns.csv",
}

# Tables partitioned as year=/month=/day=/<file>.csv (Hive-style).
_PARTITIONED_TABLES: list[str] = [
    "transactions",
    "complaints",
    "digital_events",
    "call_center_interactions",
    "satisfaction_surveys",
    "call_transcripts",
    "campaign_sends",
]

_ALL_TABLES = list(_FLAT_TABLES) + _PARTITIONED_TABLES

# Primary key column per table (None = no single PK to check)
_PRIMARY_KEYS: dict[str, str | None] = {
    "customers": "customer_id",
    "products": "product_id",
    "service_agents": "agent_id",
    "branches": "branch_id",
    "daily_exchange_rates": None,
    "marketing_campaigns": "campaign_id",
    "transactions": "transaction_id",
    "complaints": "complaint_id",
    "digital_events": "event_id",
    "call_center_interactions": "interaction_id",
    "satisfaction_surveys": "survey_id",
    "call_transcripts": "transcript_id",
    "campaign_sends": "send_id",
}

# Country columns to audit per table
_COUNTRY_COLS: dict[str, list[str]] = {
    "customers": ["country"],
    "branches": ["country"],
    "service_agents": ["country_of_origin"],
    "transactions": ["transaction_country"],
}

# Currency columns
_CURRENCY_COLS: dict[str, list[str]] = {
    "customers": [],
    "products": ["currency"],
    "complaints": ["currency"],
    "transactions": ["currency"],
    "daily_exchange_rates": ["source_currency", "target_currency"],
}

# Categorical columns to audit for unexpected values
_CATEGORICAL_COLS: dict[str, list[str]] = {
    "transactions": ["transaction_status", "transaction_type", "channel"],
    "customers": ["customer_status", "detected_accent", "segment", "document_type"],
    "call_center_interactions": ["customer_detected_accent", "channel", "contact_reason"],
    "call_transcripts": ["detected_accent", "detected_language"],
    "complaints": ["status", "case_type", "priority", "reception_channel"],
    "products": ["product_type", "product_status", "opening_channel"],
    "service_agents": ["agent_type", "experience_level"],
    "campaign_sends": ["send_status", "send_channel"],
}

# Timestamp/date columns per table + expected range
_DATE_RANGE = ("2023-06-17", "2026-06-17")
_DATE_COLS: dict[str, list[str]] = {
    "customers": ["date_of_birth", "registration_date"],
    "transactions": ["transaction_date", "process_date"],
    "products": ["opening_date", "expiration_date", "last_transaction_date"],
    "complaints": ["creation_date", "process_date", "resolution_date", "closing_date"],
    "digital_events": ["event_date", "process_date"],
    "call_center_interactions": ["interaction_date", "process_date"],
    "satisfaction_surveys": ["survey_date", "process_date"],
    "call_transcripts": ["process_date"],
    "campaign_sends": ["send_date", "process_date"],
    "branches": ["branch_opening_date"],
    "daily_exchange_rates": ["date"],
    "marketing_campaigns": ["start_date", "end_date"],
}

# Numerical columns with defined valid ranges (min, max)
_NUMERIC_RANGES: dict[str, list[tuple[str, float, float]]] = {
    "transactions": [("amount", 0.0, 1e9), ("fraud_score", 0.0, 1.0)],
    "customers": [("credit_score", 300.0, 900.0), ("estimated_monthly_income", 0.0, 1e8)],
    "products": [("current_balance", -1e9, 1e9), ("interest_rate", 0.0, 100.0), ("days_past_due", 0.0, 3650.0)],
    "call_center_interactions": [("sentiment_score", -1.0, 1.0), ("duration_seconds", 0.0, 86400.0)],
    "satisfaction_surveys": [("main_score", 0.0, 10.0)],
    "call_transcripts": [("accent_confidence", 0.0, 1.0)],
}

# PII fields per table
_PII_FIELDS: dict[str, list[str]] = {
    "customers": [
        "first_name", "last_name", "document_number", "email", "mobile_phone",
        "landline_phone", "address", "credit_score", "estimated_monthly_income",
    ],
    "service_agents": ["first_name", "last_name", "email", "phone"],
    "digital_events": ["ip_address"],
    "call_center_interactions": [],
    "call_transcripts": ["full_text", "customer_text"],
}

# Referential integrity checks (child_table, child_col, parent_table, parent_col)
_RI_CHECKS: list[tuple[str, str, str, str]] = [
    ("transactions", "customer_id", "customers", "customer_id"),
    ("transactions", "product_id", "products", "product_id"),
    ("complaints", "customer_id", "customers", "customer_id"),
    ("digital_events", "customer_id", "customers", "customer_id"),
    ("campaign_sends", "customer_id", "customers", "customer_id"),
    ("campaign_sends", "campaign_id", "marketing_campaigns", "campaign_id"),
    ("call_center_interactions", "customer_id", "customers", "customer_id"),
    ("satisfaction_surveys", "customer_id", "customers", "customer_id"),
]

# ---------------------------------------------------------------------------
# Finding dataclass
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    table: str
    column: str
    issue: str
    affected_count: int | str
    affected_pct: float | str
    proposed_rule: str


# ---------------------------------------------------------------------------
# Profiler
# ---------------------------------------------------------------------------


class RawDataProfiler:
    def __init__(self, raw_dir: Path) -> None:
        self.raw_dir = raw_dir
        self._con = duckdb.connect(":memory:")
        self.findings: list[Finding] = []
        self._table_row_counts: dict[str, int] = {}
        self._registered: set[str] = set()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _register_views(self) -> None:
        for table, csv_name in _FLAT_TABLES.items():
            csv_path = self.raw_dir / csv_name
            if csv_path.exists():
                self._con.execute(
                    f"CREATE OR REPLACE VIEW raw_{table} AS "
                    f"SELECT * FROM read_csv_auto('{csv_path}', header=true);"
                )
                self._registered.add(table)
                log.info("Registered flat view: raw_%s", table)
            else:
                log.warning("Flat CSV not found, skipping: %s", csv_path)

        for table in _PARTITIONED_TABLES:
            glob = str(self.raw_dir / table / "**" / "*.csv")
            table_dir = self.raw_dir / table
            # Fast existence check: just look for any CSV one level deep
            if not table_dir.is_dir():
                log.warning("No CSV files found for partitioned table: %s", table)
                continue
            try:
                self._con.execute(
                    f"CREATE OR REPLACE VIEW raw_{table} AS "
                    f"SELECT * FROM read_csv_auto('{glob}', union_by_name=true, header=true);"
                )
                self._registered.add(table)
                log.info("Registered partitioned view: raw_%s", table)
            except Exception as exc:
                log.warning("Could not register partitioned view raw_%s: %s", table, exc)

    def _row_count(self, table: str) -> int:
        if table not in self._table_row_counts:
            n = self._con.execute(f"SELECT COUNT(*) FROM raw_{table}").fetchone()[0]
            self._table_row_counts[table] = n
        return self._table_row_counts[table]

    def _pct(self, count: int, total: int) -> float:
        return round(count / total * 100, 2) if total else 0.0

    def _add(self, f: Finding) -> None:
        self.findings.append(f)

    # ------------------------------------------------------------------
    # Dimension 1 – Categorical & text standardisation
    # ------------------------------------------------------------------

    def _profile_categorical(self) -> None:
        log.info("=== Dimension 1: Categorical & text standardisation ===")

        # Country fields
        for table, cols in _COUNTRY_COLS.items():
            if table not in self._registered:
                continue
            total = self._row_count(table)
            for col in cols:
                rows = self._con.execute(
                    f"SELECT {col}, COUNT(*) AS n FROM raw_{table} GROUP BY {col} ORDER BY n DESC"
                ).fetchall()
                values = {str(r[0]): r[1] for r in rows}
                log.info("  [%s.%s] distinct country values: %s", table, col, list(values.keys())[:20])

                # Check for un-accented variants
                for v, cnt in values.items():
                    if v and v.strip().lower() in ("mexico", "colombia", "argentina"):
                        # These are the canonical forms – flag only non-canonical
                        canonical_map = {
                            "mexico": "México",
                            "colombia": "Colombia",
                            "argentina": "Argentina",
                        }
                        canonical = canonical_map.get(v.strip().lower())
                        if canonical and v.strip() != canonical:
                            self._add(Finding(
                                table=table, column=col,
                                issue=f"Non-canonical country name: '{v}' (expected '{canonical}')",
                                affected_count=cnt, affected_pct=self._pct(cnt, total),
                                proposed_rule=(
                                    f"CASE WHEN TRIM({col}) = '{v}' THEN '{canonical}' "
                                    f"ELSE COALESCE({col}, 'UNSPECIFIED') END AS {col}"
                                ),
                            ))

                # Check casing anomalies (mixed case vs title case)
                non_title = [(v, cnt) for v, cnt in values.items()
                             if v and v != v.strip() and v.strip()]
                for v, cnt in non_title:
                    self._add(Finding(
                        table=table, column=col,
                        issue=f"Leading/trailing whitespace in country value: '{v}'",
                        affected_count=cnt, affected_pct=self._pct(cnt, total),
                        proposed_rule=f"TRIM({col}) AS {col}",
                    ))

        # Currency fields
        valid_currencies = {"MXN", "COP", "ARS", "USD", "EUR"}
        for table, cols in _CURRENCY_COLS.items():
            if table not in self._registered:
                continue
            total = self._row_count(table)
            for col in cols:
                try:
                    rows = self._con.execute(
                        f"SELECT {col}, COUNT(*) AS n FROM raw_{table} GROUP BY {col} ORDER BY n DESC"
                    ).fetchall()
                except Exception:
                    continue
                for v, cnt in rows:
                    if v is None:
                        continue
                    if str(v).upper() not in valid_currencies:
                        self._add(Finding(
                            table=table, column=col,
                            issue=f"Unexpected currency code: '{v}'",
                            affected_count=cnt, affected_pct=self._pct(cnt, total),
                            proposed_rule=(
                                f"CASE WHEN {col} NOT IN ('MXN','COP','ARS','USD','EUR') "
                                f"THEN 'UNSPECIFIED' ELSE {col} END AS {col}"
                            ),
                        ))

        # General categoricals
        for table, cols in _CATEGORICAL_COLS.items():
            if table not in self._registered:
                continue
            total = self._row_count(table)
            for col in cols:
                try:
                    rows = self._con.execute(
                        f"SELECT {col}, COUNT(*) AS n FROM raw_{table} GROUP BY {col} ORDER BY n DESC LIMIT 50"
                    ).fetchall()
                except Exception:
                    continue
                values = [str(r[0]) for r in rows]
                log.info("  [%s.%s] distinct values (%d): %s", table, col, len(rows), values[:15])

                # Flag mixed-case or whitespace issues
                for v_raw, cnt in rows:
                    if v_raw is None:
                        continue
                    v = str(v_raw)
                    if v != v.strip():
                        self._add(Finding(
                            table=table, column=col,
                            issue=f"Whitespace in categorical value: '{v}'",
                            affected_count=cnt, affected_pct=self._pct(cnt, total),
                            proposed_rule=f"TRIM({col}) AS {col}",
                        ))

    # ------------------------------------------------------------------
    # Dimension 2 – Completeness & null patterns
    # ------------------------------------------------------------------

    def _profile_nulls(self) -> None:
        log.info("=== Dimension 2: Completeness & null pattern analysis ===")
        threshold = 5.0  # percent

        for table in self._registered:
            total = self._row_count(table)
            if total == 0:
                continue
            cols = self._con.execute(
                f"SELECT column_name FROM information_schema.columns "
                f"WHERE table_name = 'raw_{table}' ORDER BY ordinal_position"
            ).fetchall()
            col_names = [r[0] for r in cols]

            for col in col_names:
                try:
                    null_count = self._con.execute(
                        f"SELECT COUNT(*) FROM raw_{table} WHERE {col} IS NULL"
                    ).fetchone()[0]
                except Exception:
                    continue
                pct = self._pct(null_count, total)
                if pct > threshold:
                    # Suggest imputation strategy
                    if any(kw in col.lower() for kw in ("name", "type", "status", "category", "channel", "country", "currency", "accent", "reason")):
                        strategy = f"COALESCE({col}, 'UNSPECIFIED') AS {col}"
                    elif any(kw in col.lower() for kw in ("amount", "score", "balance", "rate", "count", "value")):
                        strategy = f"COALESCE({col}, 0.0) AS {col}"
                    elif any(kw in col.lower() for kw in ("date", "timestamp")):
                        strategy = f"-- Leave NULL; do not impute dates; filter downstream"
                    else:
                        strategy = f"COALESCE({col}, 'UNKNOWN') AS {col}"

                    self._add(Finding(
                        table=table, column=col,
                        issue=f"High null rate: {pct:.1f}%",
                        affected_count=null_count, affected_pct=pct,
                        proposed_rule=strategy,
                    ))
                    log.info("  [%s.%s] null=%.1f%% (%d/%d)", table, col, pct, null_count, total)

    # ------------------------------------------------------------------
    # Dimension 3 – PK uniqueness & duplication
    # ------------------------------------------------------------------

    def _profile_pk(self) -> None:
        log.info("=== Dimension 3: PK uniqueness & duplication ===")
        for table in self._registered:
            total = self._row_count(table)
            if total == 0:
                continue

            pk = _PRIMARY_KEYS.get(table)
            if pk:
                try:
                    distinct_pk = self._con.execute(
                        f"SELECT COUNT(DISTINCT {pk}) FROM raw_{table}"
                    ).fetchone()[0]
                except Exception:
                    distinct_pk = None

                if distinct_pk is not None and distinct_pk < total:
                    dup_count = total - distinct_pk
                    self._add(Finding(
                        table=table, column=pk,
                        issue=f"Duplicate PK values: {dup_count:,} extra rows ({self._pct(dup_count, total):.2f}%)",
                        affected_count=dup_count, affected_pct=self._pct(dup_count, total),
                        proposed_rule=(
                            f"SELECT DISTINCT ON ({pk}) * FROM bronze_{table} "
                            f"ORDER BY {pk}  -- or use ROW_NUMBER() with a stable tiebreak"
                        ),
                    ))
                    log.info("  [%s] PK duplicates: %d rows (%.2f%%)", table, dup_count, self._pct(dup_count, total))
                else:
                    log.info("  [%s] PK '%s' is unique across %d rows ✓", table, pk, total)

            # Exact-row duplicates
            try:
                distinct_rows = self._con.execute(
                    f"SELECT COUNT(*) FROM (SELECT DISTINCT * FROM raw_{table})"
                ).fetchone()[0]
            except Exception:
                continue
            dup_rows = total - distinct_rows
            if dup_rows > 0:
                log.info(
                    "  [%s] exact duplicate rows: %d (%.2f%%)",
                    table, dup_rows, self._pct(dup_rows, total),
                )
                self._add(Finding(
                    table=table, column="(all columns)",
                    issue=f"Exact duplicate rows: {dup_rows:,}",
                    affected_count=dup_rows, affected_pct=self._pct(dup_rows, total),
                    proposed_rule=f"SELECT DISTINCT * FROM bronze_{table}",
                ))

    # ------------------------------------------------------------------
    # Dimension 4 – Referential integrity
    # ------------------------------------------------------------------

    def _profile_ri(self) -> None:
        log.info("=== Dimension 4: Referential integrity ===")
        for child_tbl, child_col, parent_tbl, parent_col in _RI_CHECKS:
            if child_tbl not in self._registered or parent_tbl not in self._registered:
                log.warning("  Skipping RI check %s.%s → %s.%s (table not registered)",
                            child_tbl, child_col, parent_tbl, parent_col)
                continue
            try:
                orphans = self._con.execute(
                    f"""
                    SELECT COUNT(*) FROM raw_{child_tbl} c
                    WHERE c.{child_col} IS NOT NULL
                      AND c.{child_col} NOT IN (
                          SELECT {parent_col} FROM raw_{parent_tbl}
                          WHERE {parent_col} IS NOT NULL
                      )
                    """
                ).fetchone()[0]
            except Exception as exc:
                log.warning("  RI check failed for %s.%s: %s", child_tbl, child_col, exc)
                continue

            total = self._row_count(child_tbl)
            pct = self._pct(orphans, total)
            if orphans > 0:
                self._add(Finding(
                    table=child_tbl, column=child_col,
                    issue=f"Orphaned FK → {parent_tbl}.{parent_col}: {orphans:,} rows ({pct:.2f}%)",
                    affected_count=orphans, affected_pct=pct,
                    proposed_rule=(
                        f"INNER JOIN silver_{parent_tbl} p ON c.{child_col} = p.{parent_col}  "
                        f"-- or LEFT JOIN + WHERE p.{parent_col} IS NOT NULL to drop orphans"
                    ),
                ))
                log.info("  [%s.%s → %s.%s] orphans: %d (%.2f%%)",
                         child_tbl, child_col, parent_tbl, parent_col, orphans, pct)
            else:
                log.info("  [%s.%s → %s.%s] no orphans ✓",
                         child_tbl, child_col, parent_tbl, parent_col)

    # ------------------------------------------------------------------
    # Dimension 5 – Temporal & numerical range sanity
    # ------------------------------------------------------------------

    def _profile_ranges(self) -> None:
        log.info("=== Dimension 5: Temporal & numerical range sanity ===")
        lo, hi = _DATE_RANGE

        for table, cols in _DATE_COLS.items():
            if table not in self._registered:
                continue
            total = self._row_count(table)
            for col in cols:
                try:
                    row = self._con.execute(
                        f"SELECT MIN(TRY_CAST({col} AS DATE)), MAX(TRY_CAST({col} AS DATE)), "
                        f"COUNT(*) FILTER (WHERE TRY_CAST({col} AS DATE) > DATE '{hi}') AS future_rows, "
                        f"COUNT(*) FILTER (WHERE TRY_CAST({col} AS DATE) < DATE '{lo}') AS pre_range_rows "
                        f"FROM raw_{table}"
                    ).fetchone()
                except Exception as exc:
                    log.warning("  Date probe failed for %s.%s: %s", table, col, exc)
                    continue

                min_d, max_d, future_rows, pre_rows = row
                log.info("  [%s.%s] range: %s → %s  future=%d  pre-range=%d",
                         table, col, min_d, max_d, future_rows or 0, pre_rows or 0)

                if future_rows:
                    self._add(Finding(
                        table=table, column=col,
                        issue=f"Future dates beyond {hi}: {future_rows:,} rows",
                        affected_count=future_rows, affected_pct=self._pct(future_rows, total),
                        proposed_rule=(
                            f"WHERE {col} <= DATE '{hi}'  "
                            f"-- or NULLIF({col}, values > cutoff)"
                        ),
                    ))
                if pre_rows:
                    self._add(Finding(
                        table=table, column=col,
                        issue=f"Dates before {lo}: {pre_rows:,} rows",
                        affected_count=pre_rows, affected_pct=self._pct(pre_rows, total),
                        proposed_rule=(
                            f"WHERE {col} >= DATE '{lo}'  "
                            f"-- review; date_of_birth legitimately pre-dates window"
                        ),
                    ))

        for table, specs in _NUMERIC_RANGES.items():
            if table not in self._registered:
                continue
            total = self._row_count(table)
            for col, min_val, max_val in specs:
                try:
                    row = self._con.execute(
                        f"SELECT "
                        f"  COUNT(*) FILTER (WHERE TRY_CAST({col} AS DOUBLE) < {min_val}) AS below, "
                        f"  COUNT(*) FILTER (WHERE TRY_CAST({col} AS DOUBLE) > {max_val}) AS above, "
                        f"  MIN(TRY_CAST({col} AS DOUBLE)), MAX(TRY_CAST({col} AS DOUBLE)) "
                        f"FROM raw_{table}"
                    ).fetchone()
                except Exception as exc:
                    log.warning("  Numeric probe failed for %s.%s: %s", table, col, exc)
                    continue

                below, above, actual_min, actual_max = row
                log.info("  [%s.%s] min=%.4f max=%.4f  below_range=%d above_range=%d",
                         table, col, actual_min or 0, actual_max or 0, below or 0, above or 0)

                if below:
                    self._add(Finding(
                        table=table, column=col,
                        issue=f"Values below minimum ({min_val}): {below:,} rows  (actual min={actual_min})",
                        affected_count=below, affected_pct=self._pct(below, total),
                        proposed_rule=(
                            f"NULLIF(CASE WHEN {col} < {min_val} THEN NULL ELSE {col} END, NULL) AS {col}"
                        ),
                    ))
                if above:
                    self._add(Finding(
                        table=table, column=col,
                        issue=f"Values above maximum ({max_val}): {above:,} rows  (actual max={actual_max})",
                        affected_count=above, affected_pct=self._pct(above, total),
                        proposed_rule=(
                            f"NULLIF(CASE WHEN {col} > {max_val} THEN NULL ELSE {col} END, NULL) AS {col}"
                        ),
                    ))

    # ------------------------------------------------------------------
    # Dimension 6 – PII inventory
    # ------------------------------------------------------------------

    def _profile_pii(self) -> None:
        log.info("=== Dimension 6: PII field inventory ===")
        for table, pii_cols in _PII_FIELDS.items():
            if table not in self._registered:
                continue
            for col in pii_cols:
                self._add(Finding(
                    table=table, column=col,
                    issue="PII field – must be masked or dropped before Gold materialisation",
                    affected_count="ALL rows",
                    affected_pct="100%",
                    proposed_rule=(
                        f"-- DROP {col} from silver_{table} SELECT list  "
                        f"-- OR apply static hash: SHA256(CAST({col} AS VARCHAR)) AS {col}_hash"
                    ),
                ))

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(self) -> list[Finding]:
        self._register_views()
        self._profile_categorical()
        self._profile_nulls()
        self._profile_pk()
        self._profile_ri()
        self._profile_ranges()
        self._profile_pii()
        self._con.close()
        log.info("Profiling complete. Total findings: %d", len(self.findings))
        return self.findings

    def table_row_counts(self) -> dict[str, int]:
        return dict(self._table_row_counts)


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def _health_score(findings: list[Finding], total_rows_all_tables: int) -> float:
    """Simple score: 100 minus penalty per finding, weighted by affected % when numeric."""
    penalty = 0.0
    for f in findings:
        if f.issue.startswith("PII"):
            penalty += 0.5  # informational – low penalty
        elif isinstance(f.affected_pct, (int, float)):
            penalty += min(f.affected_pct * 0.3, 5.0)
        else:
            penalty += 2.0
    return max(0.0, round(100.0 - penalty, 1))


def generate_report(
    findings: list[Finding],
    row_counts: dict[str, int],
    out_path: Path,
) -> None:
    score = _health_score(findings, sum(row_counts.values()))

    lines: list[str] = []
    a = lines.append

    a("# Silver Cleaning Backlog")
    a("")
    a("> Generated by `profile_raw_data.py`  |  Dataset cutoff: 2026-06-17")
    a("")
    a("---")
    a("")
    a("## Executive Summary")
    a("")
    a(f"**Overall data health score: {score} / 100**")
    a("")
    a("| Table | Row Count | Findings |")
    a("|---|---:|---:|")
    all_tables_in_findings = {f.table for f in findings}
    for tbl in _ALL_TABLES:
        rc = row_counts.get(tbl, "—")
        n_findings = sum(1 for f in findings if f.table == tbl)
        a(f"| `{tbl}` | {rc:,} | {n_findings} |" if isinstance(rc, int) else f"| `{tbl}` | {rc} | {n_findings} |")
    a("")
    total_rows = sum(row_counts.values())
    a(f"**Total rows across all registered tables:** {total_rows:,}")
    a(f"**Total findings:** {len(findings)}")
    a("")
    a("---")
    a("")
    a("## Detailed Anomalies")
    a("")
    a("| # | Table | Column | Issue | Affected Rows / % | Proposed Silver Rule |")
    a("|---|---|---|---|---|---|")
    for i, f in enumerate(findings, 1):
        pct = f"{f.affected_pct:.2f}%" if isinstance(f.affected_pct, float) else str(f.affected_pct)
        cnt = f"{f.affected_count:,}" if isinstance(f.affected_count, int) else str(f.affected_count)
        rule = f.proposed_rule.replace("|", "\\|").replace("\n", " ")
        a(f"| {i} | `{f.table}` | `{f.column}` | {f.issue} | {cnt} / {pct} | `{rule}` |")

    a("")
    a("---")
    a("")
    a("## Recommended Silver Enhancements")
    a("")
    a("The following SQL snippets should be incorporated into `_build_silver_tables()` in `local_runner.py`.")
    a("")

    sections = {
        "Categorical & Country Standardisation": [f for f in findings if "country" in f.issue.lower() or "canonical" in f.issue.lower() or "currency" in f.issue.lower() or "whitespace" in f.issue.lower()],
        "Null / Completeness Imputation": [f for f in findings if "null rate" in f.issue.lower()],
        "Deduplication": [f for f in findings if "duplicate" in f.issue.lower()],
        "Referential Integrity Fixes": [f for f in findings if "orphan" in f.issue.lower() or "fk" in f.issue.lower()],
        "Date & Numeric Range Guards": [f for f in findings if any(kw in f.issue.lower() for kw in ("future", "below minimum", "above maximum", "pre-range", "dates before"))],
        "PII Masking / Removal": [f for f in findings if "pii" in f.issue.lower()],
    }

    for section_title, sec_findings in sections.items():
        if not sec_findings:
            continue
        a(f"### {section_title}")
        a("")
        seen: set[str] = set()
        for f in sec_findings:
            key = f"{f.table}.{f.column}"
            if key in seen:
                continue
            seen.add(key)
            a(f"**`{f.table}.{f.column}`** — {f.issue}")
            a("")
            a("```sql")
            a(f.proposed_rule)
            a("```")
            a("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report written → %s", out_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Profile raw data and generate silver cleaning backlog.")
    parser.add_argument("--raw-dir", default="data/raw/data", help="Root raw data directory")
    parser.add_argument("--out", default="silver_cleaning_backlog.md", help="Output Markdown report path")
    args = parser.parse_args(argv)

    raw_dir = Path(args.raw_dir)
    if not raw_dir.exists():
        log.error("Raw directory not found: %s", raw_dir)
        sys.exit(1)

    profiler = RawDataProfiler(raw_dir)
    findings = profiler.run()
    row_counts = profiler.table_row_counts()

    generate_report(findings, row_counts, Path(args.out))
    print(f"\nDone. {len(findings)} findings. Report: {args.out}")


if __name__ == "__main__":
    main()
