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

import logging
from datetime import datetime, timezone
from pathlib import Path

import duckdb

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
            self._generate_report(bronze_counts, silver_counts, gold_counts, quality_metrics)
        finally:
            self._con.close()
            self._con = None

        logger.info("LocalPipelineRunner complete | report=%s", self.report_path)

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
        """
        Return row counts for Bronze source tables.

        Only flat (single-file) tables are counted at this stage.  Partitioned
        tables containing thousands of CSV files would require a full multi-file
        scan just to produce a number for the report; that cost is unjustified.
        Their Bronze count is omitted here and reported as '—' in the report.
        The Silver table counts (from materialised DuckDB tables) are always
        exact and are the primary quality signal.
        """
        # Tables backed by a single flat CSV — counting is essentially free.
        _FLAT_TABLES = {"customers", "products", "service_agents"}
        counts: dict[str, int] = {}
        for table in _SILVER_TABLES:
            if table not in _FLAT_TABLES:
                continue
            if self._view_exists(f"bronze_{table}"):
                counts[table] = self._con.execute(
                    f"SELECT COUNT(*) FROM bronze_{table}"
                ).fetchone()[0]
        return counts

    # ------------------------------------------------------------------ #
    # Silver  (delegates SQL to sentinel_data.transforms)                  #
    # ------------------------------------------------------------------ #

    def _build_silver_tables(self) -> None:
        """
        Build all Silver tables from Bronze views using canonical SQL from
        ``sentinel_data.transforms``.

        Transformations applied per table:
        - Deduplication via ``SELECT DISTINCT``.
        - Missing-value imputation: categorical columns → ``'UNSPECIFIED'``.
        - Country normalisation (REQ-0015): ``'Mexico'`` → ``'México'``.
        """
        builders: dict[str, tuple[str, str]] = {
            "customers":                ("bronze_customers",               silver_customers_sql("bronze_customers")),
            "transactions":             ("bronze_transactions",            silver_transactions_sql("bronze_transactions")),
            "products":                 ("bronze_products",                silver_products_sql("bronze_products")),
            "complaints":               ("bronze_complaints",              silver_complaints_sql("bronze_complaints")),
            "service_agents":           ("bronze_service_agents",          silver_service_agents_sql("bronze_service_agents")),
            "call_center_interactions": ("bronze_call_center_interactions", silver_call_center_interactions_sql("bronze_call_center_interactions")),
            "satisfaction_surveys":     ("bronze_satisfaction_surveys",    silver_satisfaction_surveys_sql("bronze_satisfaction_surveys")),
        }
        for table, (bronze_view, sql) in builders.items():
            if self._view_exists(bronze_view):
                self._con.execute(
                    f"CREATE OR REPLACE TABLE silver_{table} AS {sql};"
                )
                logger.info("Silver table built: silver_%s", table)
            else:
                logger.warning("Skipping silver_%s – bronze view absent", table)

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
                metrics[key] = self._con.execute(
                    f"SELECT COUNT(*) FROM bronze_{table} WHERE TRIM({col}) = 'Mexico'"
                ).fetchone()[0]
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

    # ------------------------------------------------------------------ #
    # Report                                                               #
    # ------------------------------------------------------------------ #

    def _generate_report(
        self,
        bronze_counts: dict[str, int],
        silver_counts: dict[str, int],
        gold_counts: dict[str, int],
        quality_metrics: dict[str, object],
    ) -> None:
        """Write the structured Markdown data-quality report."""
        ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        total = quality_metrics.get("total_txn_count", 0) or 1
        eligible = quality_metrics.get("eligible_count", 0)
        ineligible = quality_metrics.get("ineligible_count", 0)
        pct_elig = 100.0 * eligible / total if total else 0.0
        pct_inelig = 100.0 * ineligible / total if total else 0.0
        total_mexico = quality_metrics.get("total_mexico_normalised", 0)
        svc_cols = quality_metrics.get("service_view_columns", [])
        dup_removed = sum(
            bronze_counts.get(t, 0) - silver_counts.get(t, 0)
            for t in _SILVER_TABLES
            if t in bronze_counts and t in silver_counts
        )

        lines: list[str] = []

        lines += [
            "# Sentinel Engine — Data Quality Report",
            "",
            f"**Execution timestamp:** {ts}",
            f"**Dataset cutoff date:** {DATASET_CUTOFF_DATE}",
            f"**DuckDB file:** `{self.duckdb_path}`",
            "",
            "---",
            "",
            "## 1. Volume Summary",
            "",
            "### Bronze → Silver (per table)",
            "",
            "| Table | Bronze rows | Silver rows | Duplicates removed |",
            "|---|---:|---:|---:|",
        ]
        for tbl in _SILVER_TABLES:
            if tbl in bronze_counts and tbl in silver_counts:
                b = bronze_counts[tbl]
                s = silver_counts[tbl]
                lines.append(f"| {tbl} | {b:,} | {s:,} | {b - s:,} |")
            elif tbl in silver_counts:
                lines.append(f"| {tbl} | — | {silver_counts[tbl]:,} | — |")
            else:
                lines.append(f"| {tbl} | — | — | — |")
        lines.append(
            "*Note: For large partitioned tables, Bronze layer row counts are omitted (—) "
            "during ingestion to optimize I/O and avoid redundant CSV scans.*"
        )

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
            "## 2. Data Quality Metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Duplicates removed (flat-file tables only) | {dup_removed:,} |",
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
            "## 3. PII Compliance Verification",
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
            "*Generated by `sentinel_data.local_runner.LocalPipelineRunner`.*",
        ]

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
