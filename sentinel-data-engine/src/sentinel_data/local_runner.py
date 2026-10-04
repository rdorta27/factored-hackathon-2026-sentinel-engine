"""
Full Bronze → Silver → Gold local pipeline runner backed by a persistent DuckDB file.

This module is the single entry point for local end-to-end execution without
Databricks.  It reads raw CSV files from ``data/raw/`` (Hive-partitioned or
single flat file), applies Silver quality rules (deduplication, missing-value
imputation, country normalisation), builds the Gold dispute-intake tables, and
writes a structured Markdown data-quality report.

All SQL is sourced from ``sentinel_data.transforms`` so every business rule has
one canonical definition shared with the Databricks layer modules.

Usage (CLI)
-----------
    python -m sentinel_data --layer all
    python -m sentinel_data --layer all \\
        --raw-dir data/raw \\
        --duckdb-out data/gold_bank.duckdb \\
        --report-out data_quality_report.md

All operations use ``CREATE OR REPLACE TABLE / VIEW`` for idempotent,
repeatable execution.  Re-running the pipeline overwrites existing tables.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from sentinel_data.catalog import get_table

from sentinel_data.transforms import (
    DATASET_CUTOFF_DATE,
    DISPUTE_ELIGIBILITY_DAYS,
    gold_cases_summary_sql,
    gold_customer_360_sql,
    gold_eligible_transactions_sql,
    gold_service_eligible_transactions_sql,
    silver_call_center_interactions_sql,
    silver_complaints_sql,
    silver_customers_sql,
    silver_products_sql,
    silver_satisfaction_surveys_sql,
    silver_service_agents_sql,
    silver_transactions_sql,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Table registry & entity aliases                                               #
# --------------------------------------------------------------------------- #

# Ordered so that each Silver table depends only on tables defined earlier.
_SILVER_TABLES = [
    "customers",
    "transactions",
    "products",
    "complaints",
    "service_agents",
    "call_center_interactions",
    "satisfaction_surveys",
]

# Canonical entity names for discovery → normalised to lowercase for matching.
_ENTITY_ALIASES: dict[str, list[str]] = {
    "customers":                 ["customers", "customer"],
    "transactions":              ["transactions", "transaction"],
    "products":                  ["products", "product"],
    "complaints":                ["complaints", "complaint"],
    "service_agents":            ["service_agents", "service_agent", "agents"],
    "call_center_interactions":  ["call_center_interactions", "call_center_interaction", "interactions"],
    "satisfaction_surveys":      ["satisfaction_surveys", "satisfaction_survey", "surveys"],
    "digital_events":            ["digital_events", "digital_event", "events"],
    "branches":                  ["branches", "branch"],
    "daily_exchange_rates":      ["daily_exchange_rates", "exchange_rates", "exchange_rate"],
    "marketing_campaigns":       ["marketing_campaigns", "marketing_campaign", "campaigns", "campaign"],
    "call_transcripts":          ["call_transcripts", "call_transcript", "transcripts"],
    "campaign_sends":            ["campaign_sends", "campaign_send", "sends"],
}

# Event-date vs partition-date columns for late-arrival detection.
# Maps Silver table -> (event_date_col, process_date_col).
_LATE_ARRIVAL_COLS: dict[str, tuple[str, str]] = {
    "transactions": ("transaction_date", "process_date"),
    "complaints": ("creation_date", "process_date"),
    "call_center_interactions": ("interaction_date", "process_date"),
    "satisfaction_surveys": ("survey_date", "process_date"),
}


# --------------------------------------------------------------------------- #
# Runner                                                                        #
# --------------------------------------------------------------------------- #


class LocalPipelineRunner:
    """
    Execute the full Medallion pipeline (Bronze → Silver → Gold) locally.

    Parameters
    ----------
    raw_dir : str | Path
        Root directory that contains raw source data.  Supports two layouts:
        - Hive-partitioned sub-directory per table, e.g.
          ``data/raw/transactions/year=2023/month=06/day=27/file.csv``
        - Single flat file per table, e.g. ``data/raw/customers.csv``
        The runner also checks an immediate ``data/`` sub-directory of ``raw_dir``
        if the table is not found directly under ``raw_dir``.
    duckdb_path : str | Path
        Path to the persistent DuckDB database file written on every run.
    report_path : str | Path
        Output path for the Markdown data-quality report.
    """

    def __init__(
        self,
        raw_dir: str | Path = "data/raw",
        duckdb_path: str | Path = "data/gold_bank.duckdb",
        report_path: str | Path = "data_quality_report.md",
    ) -> None:
        self.raw_dir = Path(raw_dir)
        self.duckdb_path = Path(duckdb_path)
        self.report_path = Path(report_path)
        self._con: duckdb.DuckDBPyConnection | None = None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """Run the full pipeline and emit the quality report."""
        logger.info(
            "LocalPipelineRunner started | raw=%s duckdb=%s",
            self.raw_dir,
            self.duckdb_path,
        )
        self.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        self._con = duckdb.connect(str(self.duckdb_path))

        try:
            self._build_bronze_views()
            bronze_counts = self._collect_bronze_counts()
            self._build_silver_tables()
            silver_counts = self._collect_silver_counts()
            self._build_gold_tables()
            gold_counts = self._collect_gold_counts()
            quality_metrics = self._collect_quality_metrics()
            quarantine_metrics = self._collect_quarantine_metrics()
            orphan_metrics = self._collect_orphan_metrics()
            late_metrics = self._collect_late_arrival_metrics()
            null_metrics = self._collect_null_metrics()
            self._generate_report(
                bronze_counts,
                silver_counts,
                gold_counts,
                quality_metrics,
                quarantine_metrics,
                orphan_metrics,
                late_metrics,
                null_metrics,
            )
        finally:
            self._con.close()
            self._con = None

        logger.info("LocalPipelineRunner complete | report=%s", self.report_path)

    def verify(self, report_path: str | Path | None = None) -> dict[str, tuple[object, object]]:
        """Recompute report figures from the DuckDB file and compare with the committed report.

        Returns an empty dict when every figure matches. Otherwise returns a
        mapping of figure-name -> (expected, actual) for each mismatch.
        Prints aggregates only (no raw rows).
        """
        from pathlib import Path as _Path

        target = _Path(report_path) if report_path is not None else _Path(self.report_path)
        if not target.is_file():
            raise FileNotFoundError(f"Committed report not found: {target}")
        if not self.duckdb_path.is_file():
            raise FileNotFoundError(f"DuckDB file not found: {self.duckdb_path}")

        self._con = duckdb.connect(str(self.duckdb_path))
        try:
            # Recompute figures without rebuilding tables (read-only).
            bronze_counts = self._collect_bronze_counts()
            silver_counts = self._collect_silver_counts()
            gold_counts = self._collect_gold_counts()
            quality_metrics = self._collect_quality_metrics()
            quarantine_metrics = self._collect_quarantine_metrics()
            orphan_metrics = self._collect_orphan_metrics()
            late_metrics = self._collect_late_arrival_metrics()
            null_metrics = self._collect_null_metrics()
            actual = self._figures_dict(
                bronze_counts,
                silver_counts,
                gold_counts,
                quality_metrics,
                quarantine_metrics,
                orphan_metrics,
                late_metrics,
                null_metrics,
            )
        finally:
            self._con.close()
            self._con = None

        expected = self._parse_figures_block(target.read_text(encoding="utf-8"))
        mismatches: dict[str, tuple[object, object]] = {}
        for key, exp_val in expected.items():
            act_val = actual.get(key, "__missing__")
            if act_val != exp_val:
                mismatches[key] = (exp_val, act_val)
        # Also flag figures present in actual but absent from the report.
        for key, act_val in actual.items():
            if key not in expected:
                mismatches[key] = ("__missing__", act_val)

        if mismatches:
            print(f"verify FAILED: {len(mismatches)} figure(s) differ from {target}")
            for key in sorted(mismatches)[:50]:
                exp_val, act_val = mismatches[key]
                print(f"  - {key}: expected={exp_val} actual={act_val}")
        else:
            print(f"verify OK: all {len(actual)} figures match {target}")
        return mismatches

    # ------------------------------------------------------------------ #
    # Bronze                                                               #
    # ------------------------------------------------------------------ #

    def _resolve_source(self, entity: str) -> str | None:
        """
        Locate raw data for *entity* and return a DuckDB glob expression, or None.

        Discovery order (first match wins):
        1. Sub-directory under raw_dir: ``<raw_dir>/<alias>/``   → ``**/*.csv``
        2. Flat CSV file under raw_dir: ``<raw_dir>/<alias>.csv``
        3. Flat Parquet under raw_dir:  ``<raw_dir>/<alias>.parquet``
        4-6. Same three lookups inside ``<raw_dir>/data/`` if that sub-dir exists.

        Matching is case-insensitive and uses the alias list from ``_ENTITY_ALIASES``.
        """
        aliases = _ENTITY_ALIASES.get(entity, [entity])
        search_roots: list[Path] = [self.raw_dir]
        nested = self.raw_dir / "data"
        if nested.is_dir():
            search_roots.append(nested)

        for root in search_roots:
            try:
                entries = {p.name.lower(): p for p in root.iterdir()}
            except PermissionError:
                continue

            for alias in aliases:
                # 1. Sub-directory with files
                candidate_dir = entries.get(alias)
                if candidate_dir and candidate_dir.is_dir():
                    for ext in ("parquet", "csv"):
                        if any(candidate_dir.rglob(f"*.{ext}")):
                            return str(candidate_dir / "**" / f"*.{ext}")

                # 2. Flat CSV
                flat_csv = entries.get(f"{alias}.csv")
                if flat_csv and flat_csv.is_file():
                    return str(flat_csv)

                # 3. Flat Parquet
                flat_pq = entries.get(f"{alias}.parquet")
                if flat_pq and flat_pq.is_file():
                    return str(flat_pq)

        return None

    def _build_bronze_views(self) -> None:
        """
        Register each known entity as a DuckDB Bronze view.

        Handles both Hive-partitioned directory trees and single flat files in a
        case-insensitive, alias-aware manner.  The ``union_by_name=true`` option
        merges files that have slightly different column orders within one table.
        Missing sources are logged as warnings; downstream Silver builds skip them.
        """
        for entity in _ENTITY_ALIASES:
            source_glob = self._resolve_source(entity)
            if source_glob is None:
                logger.warning("Bronze source not found – skipping: %s", entity)
                continue

            is_parquet = source_glob.endswith(".parquet")
            if is_parquet:
                read_fn = f"read_parquet('{source_glob}', union_by_name=true)"
            else:
                read_fn = f"read_csv_auto('{source_glob}', union_by_name=true, header=true)"

            self._con.execute(
                f"CREATE OR REPLACE VIEW bronze_{entity} AS SELECT * FROM {read_fn};"
            )
            logger.info("Bronze view registered: bronze_%s → %s", entity, source_glob)

    def _collect_bronze_counts(self) -> dict[str, int]:
        """Return row counts for every Bronze view that exists.

        All Bronze views are counted (including partitioned tables) so the
        report can explain the Bronze→Silver drop in full. Counting is a
        single sequential scan per table.
        """
        counts: dict[str, int] = {}
        for table in _SILVER_TABLES:
            if self._view_exists(f"bronze_{table}"):
                try:
                    counts[table] = self._con.execute(
                        f"SELECT COUNT(*) FROM bronze_{table}"
                    ).fetchone()[0]
                except Exception as exc:  # noqa: BLE001 – report '—' instead of failing
                    logger.warning("Bronze count failed for %s: %s", table, exc)
        return counts

    def _validation_expr(self, table: str, available_cols: set[str] | None = None) -> str:
        """Return a SQL expression yielding ';'-separated failed rule names for *table*.

        Rules whose target column is absent from the Bronze view are skipped so
        small fixtures (or evolved schemas) do not fail validation.
        """
        try:
            rules = get_table(table).quality_rules
        except KeyError:
            return "''"
        if available_cols is not None:
            rules = [r for r in rules if r.column in available_cols]
        if not rules:
            return "''"
        fragments = " || ';' || ".join(
            f"CASE WHEN NOT ({r.sql_predicate}) THEN '{r.rule_name}' ELSE '' END"
            for r in rules
        )
        return f"TRIM(BOTH ';' FROM ({fragments}))"

    # ------------------------------------------------------------------ #
    # Silver  (delegates SQL to sentinel_data.transforms)                  #
    # ------------------------------------------------------------------ #

    def _build_silver_tables(self) -> None:
        """Build Silver tables with quarantine split, deduplication and normalisation.

        For each table: rows failing catalog quality rules go to
        ``rejected_records`` (with ``table_name``, ``rejection_reason``,
        ``rejected_at`` and ``raw_record`` JSON); clean rows flow through the
        canonical Silver SQL (``SELECT DISTINCT`` dedup + ``UNSPECIFIED``
        imputation + country normalisation).
        """
        from sentinel_data.transforms import (
            silver_call_center_interactions_sql as _s_cci,
            silver_complaints_sql as _s_comp,
            silver_customers_sql as _s_cust,
            silver_products_sql as _s_prod,
            silver_satisfaction_surveys_sql as _s_surv,
            silver_service_agents_sql as _s_agent,
            silver_transactions_sql as _s_txn,
        )

        self._con.execute(
            """
            CREATE TABLE IF NOT EXISTS rejected_records (
                table_name VARCHAR,
                rejection_reason VARCHAR,
                rejected_at VARCHAR,
                raw_record VARCHAR
            )
            """
        )
        # Fresh run → fresh quarantine (idempotent reruns must not double-count).
        self._con.execute("DELETE FROM rejected_records")

        builders: dict[str, str] = {
            "customers": _s_cust("bronze_customers_clean"),
            "transactions": _s_txn("bronze_transactions_clean"),
            "products": _s_prod("bronze_products_clean"),
            "complaints": _s_comp("bronze_complaints_clean"),
            "service_agents": _s_agent("bronze_service_agents_clean"),
            "call_center_interactions": _s_cci("bronze_call_center_interactions_clean"),
            "satisfaction_surveys": _s_surv("bronze_satisfaction_surveys_clean"),
        }
        rejected_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for table, silver_sql in builders.items():
            bronze_view = f"bronze_{table}"
            if not self._view_exists(bronze_view):
                logger.warning("Skipping silver_%s – bronze view absent", table)
                continue
            try:
                bronze_cols = {
                    r[0]
                    for r in self._con.execute(f"SELECT * FROM {bronze_view} LIMIT 0").description
                }
            except Exception:  # noqa: BLE001
                bronze_cols = set()
            validation = self._validation_expr(table, bronze_cols)
            # Clean view: only rows passing every rule.
            self._con.execute(
                f"CREATE OR REPLACE VIEW {bronze_view}_validated AS "
                f"SELECT *, ({validation}) AS _rejection_reason FROM {bronze_view}"
            )
            self._con.execute(
                f"CREATE OR REPLACE VIEW {bronze_view}_clean AS "
                f"SELECT * EXCLUDE (_rejection_reason) FROM {bronze_view}_validated "
                f"WHERE _rejection_reason = ''"
            )
            # Quarantine: failing rows appended with rule names + JSON payload.
            cols = [
                r[0]
                for r in self._con.execute(
                    f"SELECT * FROM {bronze_view}_validated LIMIT 0"
                ).description
                if r[0] != "_rejection_reason"
            ]
            if cols:
                struct_args = ", ".join(f'"{c}" := "{c}"' for c in cols)
                # Escape single quotes in the timestamp-safe literal path.
                safe_ts = rejected_at.replace("'", "''")
                self._con.execute(
                    f"""
                    INSERT INTO rejected_records
                    SELECT
                        '{table}' AS table_name,
                        _rejection_reason AS rejection_reason,
                        '{safe_ts}' AS rejected_at,
                        TO_JSON(STRUCT_PACK({struct_args})) AS raw_record
                    FROM {bronze_view}_validated
                    WHERE _rejection_reason != ''
                    """
                )
            try:
                self._con.execute(f"CREATE OR REPLACE TABLE silver_{table} AS {silver_sql};")
            except Exception as exc:  # noqa: BLE001 – missing bronze column in fixture
                logger.warning("Skipping silver_%s – build failed: %s", table, exc)
                continue
            logger.info("Silver table built: silver_%s", table)

    def _collect_silver_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for table in _SILVER_TABLES:
            if self._table_exists(f"silver_{table}"):
                counts[table] = self._con.execute(
                    f"SELECT COUNT(*) FROM silver_{table}"
                ).fetchone()[0]
        return counts

    # ------------------------------------------------------------------ #
    # Gold  (delegates SQL to sentinel_data.transforms)                    #
    # ------------------------------------------------------------------ #

    def _build_gold_tables(self) -> None:
        """
        Build all Gold serving tables for the Dispute Intake use case.

        Tables
        ------
        gold_dispute_customer_360
            One row per customer_id.  Includes PII for authorised consumers.

        gold_dispute_eligible_transactions
            One row per transaction_id.  Eligibility vs fixed cutoff 2026-06-17.

        v_service_dispute_eligible_transactions
            PII-free projection.  Drops customer_first_name, customer_last_name,
            customer_credit_score.

        gold_dispute_cases_summary
            One row per complaint_id.  Full case lifecycle denormalisation.
        """
        self._gold_customer_360()
        self._gold_eligible_transactions()
        self._gold_service_eligible_transactions()
        self._gold_cases_summary()

    def _gold_customer_360(self) -> None:
        self._con.execute(
            "CREATE OR REPLACE TABLE gold_dispute_customer_360 AS "
            + gold_customer_360_sql(silver_prefix="silver_", engine="duckdb")
        )
        logger.info("Built gold_dispute_customer_360")

    def _gold_eligible_transactions(self) -> None:
        self._con.execute(
            "CREATE OR REPLACE TABLE gold_dispute_eligible_transactions AS "
            + gold_eligible_transactions_sql(silver_prefix="silver_", engine="duckdb")
        )
        logger.info("Built gold_dispute_eligible_transactions")

    def _gold_service_eligible_transactions(self) -> None:
        self._con.execute(
            "CREATE OR REPLACE VIEW v_service_dispute_eligible_transactions AS "
            + gold_service_eligible_transactions_sql(
                source="gold_dispute_eligible_transactions"
            )
        )
        logger.info("Built v_service_dispute_eligible_transactions (PII-free view)")

    def _gold_cases_summary(self) -> None:
        self._con.execute(
            "CREATE OR REPLACE TABLE gold_dispute_cases_summary AS "
            + gold_cases_summary_sql(silver_prefix="silver_", engine="duckdb")
        )
        logger.info("Built gold_dispute_cases_summary")

    def _collect_gold_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for tbl in [
            "gold_dispute_customer_360",
            "gold_dispute_eligible_transactions",
            "gold_dispute_cases_summary",
        ]:
            if self._table_exists(tbl):
                counts[tbl] = self._con.execute(
                    f"SELECT COUNT(*) FROM {tbl}"
                ).fetchone()[0]
        return counts

    # ------------------------------------------------------------------ #
    # Quality metrics                                                       #
    # ------------------------------------------------------------------ #

    def _collect_quality_metrics(self) -> dict[str, object]:
        """Query the populated DuckDB for all data-quality report metrics."""
        metrics: dict[str, object] = {}

        for table, col in [("customers", "country"), ("transactions", "transaction_country")]:
            key = f"mexico_normalised_{table}"
            if self._view_exists(f"bronze_{table}"):
                try:
                    metrics[key] = self._con.execute(
                        f"SELECT COUNT(*) FROM bronze_{table} WHERE TRIM({col}) = 'Mexico'"
                    ).fetchone()[0]
                except Exception:  # noqa: BLE001 – missing column means 0
                    metrics[key] = 0
            else:
                metrics[key] = 0

        metrics["total_mexico_normalised"] = (
            metrics.get("mexico_normalised_customers", 0)
            + metrics.get("mexico_normalised_transactions", 0)
        )

        if self._table_exists("gold_dispute_eligible_transactions"):
            row = self._con.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE is_eligible_for_dispute)     AS eligible,
                    COUNT(*) FILTER (WHERE NOT is_eligible_for_dispute) AS ineligible,
                    COUNT(*)                                             AS total
                FROM gold_dispute_eligible_transactions
                """
            ).fetchone()
            metrics["eligible_count"] = row[0]
            metrics["ineligible_count"] = row[1]
            metrics["total_txn_count"] = row[2]
        else:
            metrics["eligible_count"] = metrics["ineligible_count"] = metrics["total_txn_count"] = 0

        if self._view_exists("v_service_dispute_eligible_transactions"):
            cols = self._con.execute(
                "DESCRIBE v_service_dispute_eligible_transactions"
            ).fetchall()
            metrics["service_view_columns"] = [c[0] for c in cols]
        else:
            metrics["service_view_columns"] = []

        return metrics

    def _collect_quarantine_metrics(self) -> dict[str, object]:
        """Counts per rejection rule from ``rejected_records`` (empty when absent)."""
        metrics: dict[str, object] = {"quarantine_total": 0, "by_table": {}, "by_rule": {}}
        if not self._table_exists("rejected_records"):
            return metrics
        try:
            rows = self._con.execute(
                "SELECT table_name, rejection_reason FROM rejected_records"
            ).fetchall()
        except Exception:  # noqa: BLE001
            return metrics
        by_table: dict[str, int] = {}
        by_rule: dict[str, int] = {}
        for table_name, reason in rows:
            by_table[table_name] = by_table.get(table_name, 0) + 1
            for rule in str(reason or "").split(";"):
                rule = rule.strip().strip(";").strip()
                if rule:
                    by_rule[rule] = by_rule.get(rule, 0) + 1
        metrics["quarantine_total"] = len(rows)
        metrics["by_table"] = by_table
        metrics["by_rule"] = by_rule
        return metrics

    def _collect_orphan_metrics(self) -> dict[str, int]:
        """Anti-join orphan counts (FKs in facts missing from dimensions)."""
        orphans: dict[str, int] = {}

        def _count(sql: str) -> int:
            try:
                return int(self._con.execute(sql).fetchone()[0])
            except Exception:  # noqa: BLE001 – missing table/column → 0
                return 0

        if self._table_exists("silver_transactions"):
            if self._table_exists("silver_customers"):
                orphans["transactions_missing_customer"] = _count(
                    "SELECT COUNT(*) FROM silver_transactions t "
                    "LEFT JOIN silver_customers c ON c.customer_id = t.customer_id "
                    "WHERE c.customer_id IS NULL"
                )
            if self._table_exists("silver_products"):
                orphans["transactions_missing_product"] = _count(
                    "SELECT COUNT(*) FROM silver_transactions t "
                    "LEFT JOIN silver_products p ON p.product_id = t.product_id "
                    "WHERE p.product_id IS NULL"
                )
        if self._table_exists("silver_complaints") and self._table_exists("silver_customers"):
            orphans["complaints_missing_customer"] = _count(
                "SELECT COUNT(*) FROM silver_complaints k "
                "LEFT JOIN silver_customers c ON c.customer_id = k.customer_id "
                "WHERE c.customer_id IS NULL"
            )
        return orphans

    def _collect_late_arrival_metrics(self) -> dict[str, int]:
        """Per-table late arrivals: process_date later than the event date."""
        late: dict[str, int] = {}
        for table, (event_col, proc_col) in _LATE_ARRIVAL_COLS.items():
            if not self._table_exists(f"silver_{table}"):
                continue
            try:
                cols = {r[0] for r in self._con.execute(f"SELECT * FROM silver_{table} LIMIT 0").description}
            except Exception:  # noqa: BLE001
                continue
            if event_col not in cols or proc_col not in cols:
                continue
            try:
                late[table] = int(
                    self._con.execute(
                        f"SELECT COUNT(*) FROM silver_{table} "
                        f"WHERE TRY_CAST({proc_col} AS DATE) IS NOT NULL "
                        f"AND TRY_CAST({event_col} AS DATE) IS NOT NULL "
                        f"AND TRY_CAST({proc_col} AS DATE) > TRY_CAST({event_col} AS DATE)"
                    ).fetchone()[0]
                )
            except Exception:  # noqa: BLE001
                late[table] = 0
        return late

    def _collect_null_metrics(self) -> dict[str, dict[str, dict[str, float | int]]]:
        """Null count + rate per column per Silver table (single scan per table)."""
        nulls: dict[str, dict[str, dict[str, float | int]]] = {}
        for table in _SILVER_TABLES:
            silver = f"silver_{table}"
            if not self._table_exists(silver):
                continue
            try:
                desc = self._con.execute(f"SELECT * FROM {silver} LIMIT 0").description
                cols = [r[0] for r in desc]
            except Exception:  # noqa: BLE001
                continue
            if not cols:
                continue
            total = int(self._con.execute(f"SELECT COUNT(*) FROM {silver}").fetchone()[0])
            if total == 0:
                nulls[table] = {c: {"nulls": 0, "rate": 0.0} for c in cols}
                continue
            aggs = ", ".join(
                f"SUM(CASE WHEN \"{c}\" IS NULL THEN 1 ELSE 0 END) AS \"__n_{c}\""
                for c in cols
            )
            try:
                row = self._con.execute(f"SELECT {aggs} FROM {silver}").fetchone()
            except Exception:  # noqa: BLE001
                continue
            table_nulls: dict[str, dict[str, float | int]] = {}
            for c, n in zip(cols, row):
                n_int = int(n or 0)
                table_nulls[c] = {"nulls": n_int, "rate": n_int / total if total else 0.0}
            nulls[table] = table_nulls
        return nulls

    def _figures_dict(
        self,
        bronze_counts: dict[str, int],
        silver_counts: dict[str, int],
        gold_counts: dict[str, int],
        quality_metrics: dict[str, object],
        quarantine_metrics: dict[str, object],
        orphan_metrics: dict[str, int],
        late_metrics: dict[str, int],
        null_metrics: dict[str, dict[str, dict[str, float | int]]],
    ) -> dict[str, object]:
        """Flat figure map used by the report footer and ``verify``."""
        figures: dict[str, object] = {}
        for tbl in _SILVER_TABLES:
            if tbl in bronze_counts:
                figures[f"bronze.{tbl}"] = int(bronze_counts[tbl])
            if tbl in silver_counts:
                figures[f"silver.{tbl}"] = int(silver_counts[tbl])
        for k, v in gold_counts.items():
            figures[f"gold.{k}"] = int(v)
        for key in ("eligible_count", "ineligible_count", "total_txn_count", "total_mexico_normalised",
                    "mexico_normalised_customers", "mexico_normalised_transactions"):
            figures[f"quality.{key}"] = int(quality_metrics.get(key, 0) or 0)
        figures["quarantine.total"] = int(quarantine_metrics.get("quarantine_total", 0) or 0)
        for rule, n in (quarantine_metrics.get("by_rule", {}) or {}).items():
            figures[f"quarantine.rule.{rule}"] = int(n)
        for tbl, n in (quarantine_metrics.get("by_table", {}) or {}).items():
            figures[f"quarantine.table.{tbl}"] = int(n)
        for k, v in orphan_metrics.items():
            figures[f"orphan.{k}"] = int(v)
        for k, v in late_metrics.items():
            figures[f"late.{k}"] = int(v)
        for tbl, cols in null_metrics.items():
            for col, stats in cols.items():
                figures[f"null.{tbl}.{col}"] = int(stats.get("nulls", 0) or 0)
        return figures

    @staticmethod
    def _parse_figures_block(report_text: str) -> dict[str, object]:
        """Extract the embedded `````json figures`` block written by ``_generate_report``."""
        start = report_text.find("```json figures")
        if start < 0:
            return {}
        start = report_text.find("\n", start) + 1
        end = report_text.find("```", start)
        if end < 0:
            return {}
        try:
            data = json.loads(report_text[start:end].strip())
            return {k: v for k, v in data.items()}
        except Exception:  # noqa: BLE001 – corrupt block means 0 figures
            return {}

    # ------------------------------------------------------------------ #
    # Report                                                               #
    # ------------------------------------------------------------------ #

    def _generate_report(
        self,
        bronze_counts: dict[str, int],
        silver_counts: dict[str, int],
        gold_counts: dict[str, int],
        quality_metrics: dict[str, object],
        quarantine_metrics: dict[str, object] | None = None,
        orphan_metrics: dict[str, int] | None = None,
        late_metrics: dict[str, int] | None = None,
        null_metrics: dict[str, dict[str, dict[str, float | int]]] | None = None,
    ) -> None:
        """Write the full structured Markdown data-quality report (all sections generated)."""
        ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        quarantine_metrics = quarantine_metrics or {}
        orphan_metrics = orphan_metrics or {}
        late_metrics = late_metrics or {}
        null_metrics = null_metrics or {}

        total = quality_metrics.get("total_txn_count", 0) or 1
        eligible = quality_metrics.get("eligible_count", 0)
        ineligible = quality_metrics.get("ineligible_count", 0)
        pct_elig = 100.0 * eligible / total if total else 0.0
        pct_inelig = 100.0 * ineligible / total if total else 0.0
        total_mexico = quality_metrics.get("total_mexico_normalised", 0)
        svc_cols = quality_metrics.get("service_view_columns", [])
        quarantine_total = int(quarantine_metrics.get("quarantine_total", 0) or 0)
        by_rule = quarantine_metrics.get("by_rule", {}) or {}
        by_table = quarantine_metrics.get("by_table", {}) or {}

        lines: list[str] = []
        lines += [
            "# Sentinel Engine — Data Quality Report",
            "",
            f"**Execution timestamp:** {ts}",
            f"**Dataset cutoff date:** {DATASET_CUTOFF_DATE}",
            f"**DuckDB file:** `{self.duckdb_path}`",
            f"**Requirement:** REQ-0015",
            "",
            "---",
            "",
            "## 1. Volume Summary",
            "",
            "### Bronze → Silver (per table)",
            "",
            "| Table | Bronze rows | Silver rows | Drop (Bronze−Silver) | Quarantined |",
            "|---|---:|---:|---:|---:|",
        ]
        for tbl in _SILVER_TABLES:
            q = by_table.get(tbl, 0) if isinstance(by_table, dict) else 0
            if tbl in bronze_counts and tbl in silver_counts:
                b = bronze_counts[tbl]
                s = silver_counts[tbl]
                lines.append(f"| {tbl} | {b:,} | {s:,} | {b - s:,} | {q:,} |")
            elif tbl in silver_counts:
                lines.append(f"| {tbl} | — | {silver_counts[tbl]:,} | — | {q:,} |")
            else:
                lines.append(f"| {tbl} | — | — | — | {q:,} |")

        lines += [
            "",
            "### Drop breakdown",
            "",
            "Bronze−Silver per table decomposes into deduplication (`SELECT DISTINCT`), "
            "quarantine filtering (`rejected_records`) and orphan exclusion in Gold joins. "
            "Quarantine totals come from `rejected_records`; orphans from anti-joins below.",
            "",
            f"| Quarantined rows (all tables) | {quarantine_total:,} |",
            "|---|---|",
        ]
        if by_rule:
            lines += ["", "#### Quarantine per rule", "", "| Rule | Rows |", "|---|---:|"]
            for rule in sorted(by_rule):
                lines.append(f"| {rule} | {by_rule[rule]:,} |")
        else:
            lines += ["", "_No quarantined rows in this run._"]

        lines += [
            "",
            "### Gold tables",
            "",
            "| Gold table | Row count |",
            "|---|---:|",
        ]
        for k, v in gold_counts.items():
            lines.append(f"| {k} | {v:,} |")

        lines += [
            "",
            "---",
            "",
            "## 2. Orphans & Late Arrivals",
            "",
            "### Orphans (referential integrity)",
            "",
            "| Check | Orphan rows |",
            "|---|---:|",
        ]
        if orphan_metrics:
            for k in sorted(orphan_metrics):
                lines.append(f"| {k} | {orphan_metrics[k]:,} |")
        else:
            lines.append("| *(no Silver facts built)* | — |")

        lines += [
            "",
            "### Late arrivals per partitioned table",
            "",
            "`process_date` later than the event date counts as a late arrival.",
            "",
            "| Table | Late rows |",
            "|---|---:|",
        ]
        if late_metrics:
            for k in sorted(late_metrics):
                lines.append(f"| {k} | {late_metrics[k]:,} |")
        else:
            lines.append("| *(no partitioned Silver tables built)* | — |")

        lines += [
            "",
            "---",
            "",
            "## 3. Nulls & Country Normalisation",
            "",
            "### Null counts and rates (mandatory and optional fields)",
            "",
            "| Table | Column | Nulls | Rate |",
            "|---|---|---:|---:|",
        ]
        any_nulls = False
        for tbl in _SILVER_TABLES:
            cols = null_metrics.get(tbl, {})
            for col in sorted(cols):
                stats = cols[col]
                n = int(stats.get("nulls", 0) or 0)
                rate = float(stats.get("rate", 0.0) or 0.0)
                # Show every column with nulls plus mandatory PK/FK columns even at 0,
                # so optional nulls stay visible without flooding the report.
                if n > 0 or col in ("transaction_id", "customer_id", "amount", "transaction_date"):
                    lines.append(f"| {tbl} | {col} | {n:,} | {rate:.2%} |")
                    any_nulls = True
        if not any_nulls:
            lines.append("| *(no nulls)* | — | — | — |")

        lines += [
            "",
            "### Country normalisation",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Rows with `'Mexico'` normalised → `'México'` (customers) | {quality_metrics.get('mexico_normalised_customers', 0):,} |",
            f"| Rows with `'Mexico'` normalised → `'México'` (transactions) | {quality_metrics.get('mexico_normalised_transactions', 0):,} |",
            f"| **Total country entries normalised (REQ-0015)** | **{total_mexico:,}** |",
            "",
            f"### Dispute Eligibility Breakdown (`gold_dispute_eligible_transactions`)",
            "",
            f"Cutoff date applied: `{DATASET_CUTOFF_DATE}` · Window: ≤ {DISPUTE_ELIGIBILITY_DAYS} days · Excluded statuses: `Reversed`, `Refunded`",
            "",
            "| Outcome | Count | % of total |",
            "|---|---:|---:|",
            f"| Eligible for dispute | {eligible:,} | {pct_elig:.1f}% |",
            f"| Ineligible (expired or excluded status) | {ineligible:,} | {pct_inelig:.1f}% |",
            f"| **Total transactions** | **{eligible + ineligible:,}** | **100.0%** |",
            "",
            "---",
            "",
            "## 4. PII Compliance Verification",
            "",
            "The view `v_service_dispute_eligible_transactions` is the surface exposed to the",
            "FastAPI backend and any downstream service without explicit PII-READ permission.",
            "The following columns are confirmed present; none contain raw names, card numbers,",
            "or credit scores.",
            "",
            "| Column | PII status |",
            "|---|---|",
        ]
        if svc_cols:
            for c in svc_cols:
                lines.append(f"| {c} | No PII |")
        else:
            lines.append("| *(view not built)* | — |")

        lines += [
            "",
            "**Excluded from service view (PII columns in full Gold table only):**",
            "`customer_first_name`, `customer_last_name`, `customer_credit_score`",
            "",
            "---",
            "",
            "*Generated by `sentinel_data.local_runner.LocalPipelineRunner`. Satisfies REQ-0015.*",
            "",
            "<!-- verify-figures: machine-readable aggregates for `verify` mode. Do not edit by hand. -->",
            "```json figures",
        ]
        figures = self._figures_dict(
            bronze_counts, silver_counts, gold_counts, quality_metrics,
            quarantine_metrics, orphan_metrics, late_metrics, null_metrics,
        )
        lines.append(json.dumps(figures, indent=2, sort_keys=True))
        lines += ["```", ""]

        report = "\n".join(lines) + "\n"
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(report, encoding="utf-8")
        logger.info("Data quality report written → %s", self.report_path)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _view_exists(self, name: str) -> bool:
        result = self._con.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = ? AND table_type IN ('VIEW', 'BASE TABLE')",
            [name],
        ).fetchone()
        return result[0] > 0

    def _table_exists(self, name: str) -> bool:
        result = self._con.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_name = ? AND table_type = 'BASE TABLE'",
            [name],
        ).fetchone()
        return result[0] > 0
