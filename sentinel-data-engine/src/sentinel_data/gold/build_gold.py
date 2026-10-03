"""
Gold layer builder – denormalized, query-optimized serving tables.

Use case: Real-Time Transaction Dispute Intake & Resolution
-----------------------------------------------------------
The three Gold tables produced here are consumed directly by:
  - FastAPI backend endpoints (O(1) point-lookups by business key)
  - LLM Orchestrators / RAG tool calls that require immediate customer and
    transaction context without runtime join overhead

Gold tables are rebuilt deterministically on every run.  In local mode the
target directory is overwritten.  In Databricks mode a Delta MERGE on the
business primary key ensures idempotency.

All SQL is delegated to ``sentinel_data.transforms`` so every business rule
has one canonical definition shared with ``local_runner.py``.

Tables built
------------
gold_dispute_customer_360
    One row per customer_id.  Aggregates products, complaints, surveys.
    Derived: dispute_risk_level, total_claimed_amount.

gold_dispute_eligible_transactions
    One row per transaction_id.  Flags: is_disputed, days_since_transaction,
    is_eligible_for_dispute.  Eligibility uses fixed cutoff 2026-06-17.

gold_dispute_cases_summary
    One row per complaint_id.  Joins complaints → customers → products →
    service_agents → call_center_interactions (via origin_interaction_id).

Execution engines
-----------------
Local mode      : DuckDB (delta extension), reads ./data/silver/<table>/
                  and writes ./data/gold/<table>/ with OVERWRITE semantics.
Databricks mode : PySpark SQL + Delta MERGE on Unity Catalog managed tables.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import duckdb
import pyarrow as pa
from deltalake import write_deltalake
from pydantic import BaseModel, ConfigDict, Field

from sentinel_data.catalog import RunMode
from sentinel_data.transforms import (
    DATASET_CUTOFF_DATE,
    DISPUTE_ELIGIBILITY_DAYS,
    gold_cases_summary_sql,
    gold_customer_360_sql,
    gold_eligible_transactions_sql,
    gold_service_eligible_transactions_sql,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class GoldBuilderConfig(BaseModel):
    """Runtime parameters shared by all three Gold build steps."""

    run_mode: RunMode = Field(RunMode.LOCAL)

    # Local paths
    local_silver_dir: Path = Field(Path("data/silver"))
    local_gold_dir: Path = Field(Path("data/gold"))

    # Databricks / Unity Catalog
    databricks_catalog: str = Field("sentinel")
    databricks_schema_silver: str = Field("silver")
    databricks_schema_gold: str = Field("gold")

    model_config = ConfigDict(use_enum_values=True)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class GoldBuilder:
    """
    Build all Gold serving tables for the Dispute Intake use case.

    Parameters
    ----------
    config : GoldBuilderConfig
        Runtime configuration (run mode, path/catalog overrides).

    Examples
    --------
    Local run::

        cfg = GoldBuilderConfig()
        GoldBuilder(cfg).run()

    Databricks run::

        cfg = GoldBuilderConfig(run_mode=RunMode.DATABRICKS)
        GoldBuilder(cfg).run(spark=spark)
    """

    def __init__(self, config: GoldBuilderConfig) -> None:
        self.cfg = config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, spark: Optional[object] = None) -> None:
        """Build all Gold tables using the configured execution engine."""
        logger.info("Gold build started | mode=%s", self.cfg.run_mode)
        if self.cfg.run_mode == RunMode.LOCAL:
            self._run_local()
        else:
            if spark is None:
                raise ValueError("A SparkSession is required in DATABRICKS run mode.")
            self._run_databricks(spark)

    # ------------------------------------------------------------------
    # Local mode – DuckDB → Delta
    # ------------------------------------------------------------------

    def _run_local(self) -> None:
        """Build all Gold tables with DuckDB, overwriting local Delta directories."""
        silver = self.cfg.local_silver_dir.resolve()
        gold = self.cfg.local_gold_dir.resolve()
        gold.mkdir(parents=True, exist_ok=True)

        con = duckdb.connect()
        con.execute("INSTALL delta; LOAD delta;")

        self._local_load_silver_views(con, silver)
        self._local_build_customer_360(con, gold)
        self._local_build_eligible_transactions(con, gold)
        self._local_build_service_eligible_transactions(con, gold)
        self._local_build_cases_summary(con, gold)

        con.close()
        logger.info("Gold local build complete | gold_dir=%s", gold)

    def _local_load_silver_views(
        self, con: duckdb.DuckDBPyConnection, silver: Path
    ) -> None:
        """Register each Silver Delta table as a DuckDB view for SQL reuse."""
        tables = [
            "customers",
            "products",
            "complaints",
            "transactions",
            "service_agents",
            "call_center_interactions",
            "satisfaction_surveys",
        ]
        for tbl in tables:
            path = str(silver / tbl)
            if Path(path).exists() and any(Path(path).iterdir()):
                con.execute(
                    f"CREATE OR REPLACE VIEW silver_{tbl} AS "
                    f"SELECT * FROM delta_scan('{path}');"
                )
            else:
                logger.warning(
                    "Silver table not found – Gold queries referencing it will fail: %s", path
                )

    def _local_build_customer_360(
        self, con: duckdb.DuckDBPyConnection, gold: Path
    ) -> None:
        """
        Build gold_dispute_customer_360 (1 row per customer_id).

        Aggregates: products (count, balance), complaints (active disputes,
        total claimed, repeat flag), surveys (avg CSAT).
        Derived: dispute_risk_level.
        Fixed snapshot_date: 2026-06-17.
        """
        out_path = str(gold / "gold_dispute_customer_360")
        arrow_table: pa.Table = con.execute(
            gold_customer_360_sql(silver_prefix="silver_", engine="duckdb")
        ).fetch_arrow_table()
        write_deltalake(out_path, arrow_table, mode="overwrite")
        logger.info("Built gold_dispute_customer_360 → %s", out_path)

    def _local_build_eligible_transactions(
        self, con: duckdb.DuckDBPyConnection, gold: Path
    ) -> None:
        """
        Build gold_dispute_eligible_transactions (1 row per transaction_id).

        is_disputed: True when an open complaint shares customer_id + product_id
                     with this transaction (no referenced_transaction_id in raw).
        days_since_transaction: days from transaction_date to cutoff 2026-06-17.
        is_eligible_for_dispute: NOT disputed AND days <= 90 AND status not excluded.
        """
        out_path = str(gold / "gold_dispute_eligible_transactions")
        eligible_arrow: pa.Table = con.execute(
            gold_eligible_transactions_sql(silver_prefix="silver_", engine="duckdb")
        ).fetch_arrow_table()
        write_deltalake(out_path, eligible_arrow, mode="overwrite")
        logger.info("Built gold_dispute_eligible_transactions → %s", out_path)

    def _local_build_service_eligible_transactions(
        self, con: duckdb.DuckDBPyConnection, gold: Path
    ) -> None:
        """
        Build v_service_dispute_eligible_transactions (PII-free service projection).

        Drops customer_first_name, customer_last_name, customer_credit_score
        in compliance with ADR 008.
        """
        gold_src = str(gold / "gold_dispute_eligible_transactions")
        out_path = str(gold / "v_service_dispute_eligible_transactions")

        if not Path(gold_src).exists() or not any(Path(gold_src).iterdir()):
            logger.warning(
                "gold_dispute_eligible_transactions not found – "
                "skipping service view build: %s",
                gold_src,
            )
            return

        service_arrow: pa.Table = con.execute(
            gold_service_eligible_transactions_sql(
                source=f"delta_scan('{gold_src}')"
            )
        ).fetch_arrow_table()
        write_deltalake(out_path, service_arrow, mode="overwrite")
        logger.info("Built v_service_dispute_eligible_transactions → %s", out_path)

    def _local_build_cases_summary(
        self, con: duckdb.DuckDBPyConnection, gold: Path
    ) -> None:
        """
        Build gold_dispute_cases_summary (1 row per complaint_id).

        Joins via silver_complaints.origin_interaction_id →
        silver_call_center_interactions.interaction_id.
        Fixed snapshot_date: 2026-06-17.
        """
        out_path = str(gold / "gold_dispute_cases_summary")
        cases_arrow: pa.Table = con.execute(
            gold_cases_summary_sql(silver_prefix="silver_", engine="duckdb")
        ).fetch_arrow_table()
        write_deltalake(out_path, cases_arrow, mode="overwrite")
        logger.info("Built gold_dispute_cases_summary → %s", out_path)

    # ------------------------------------------------------------------
    # Cloud mode – PySpark SQL + Delta MERGE
    # ------------------------------------------------------------------

    def _run_databricks(self, spark: object) -> None:
        """
        Build all Gold tables on Databricks using PySpark SQL and Delta MERGE.

        Each Gold table is materialised as a temporary view then MERGE'd into
        the target Unity Catalog Delta table on its primary key.
        """
        from pyspark.sql import SparkSession  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        cat = self.cfg.databricks_catalog
        s_silver = self.cfg.databricks_schema_silver
        s_gold = self.cfg.databricks_schema_gold

        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {cat}.{s_gold}")

        self._databricks_build_customer_360(spark, cat, s_silver, s_gold)
        self._databricks_build_eligible_transactions(spark, cat, s_silver, s_gold)
        self._databricks_build_cases_summary(spark, cat, s_silver, s_gold)

        logger.info("Gold Databricks build complete | catalog=%s schema=%s", cat, s_gold)

    @staticmethod
    def _databricks_merge(
        spark: object,
        src_view: str,
        target_table: str,
        merge_on: str,
    ) -> None:
        """MERGE *src_view* rows into *target_table* on *merge_on*; create if absent."""
        from pyspark.sql import SparkSession  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        if not spark.catalog.tableExists(target_table):
            spark.sql(f"CREATE TABLE {target_table} AS SELECT * FROM {src_view}")
            logger.info("Created Gold table: %s", target_table)
        else:
            spark.sql(
                f"""
                MERGE INTO {target_table} AS target
                USING {src_view} AS source
                ON {merge_on}
                WHEN MATCHED THEN UPDATE SET *
                WHEN NOT MATCHED THEN INSERT *
                """
            )
            logger.info("Merged into Gold table: %s", target_table)

    def _databricks_build_customer_360(
        self, spark: object, cat: str, s_silver: str, s_gold: str
    ) -> None:
        from pyspark.sql import SparkSession  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        silver_prefix = f"{cat}.{s_silver}."
        sql = gold_customer_360_sql(silver_prefix=silver_prefix, engine="databricks")
        spark.sql(
            f"CREATE OR REPLACE TEMPORARY VIEW gold_customer_360_src AS {sql}"
        )
        self._databricks_merge(
            spark,
            src_view="gold_customer_360_src",
            target_table=f"{cat}.{s_gold}.gold_dispute_customer_360",
            merge_on="target.customer_id = source.customer_id",
        )

    def _databricks_build_eligible_transactions(
        self, spark: object, cat: str, s_silver: str, s_gold: str
    ) -> None:
        from pyspark.sql import SparkSession  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        silver_prefix = f"{cat}.{s_silver}."
        sql = gold_eligible_transactions_sql(silver_prefix=silver_prefix, engine="databricks")
        spark.sql(
            f"CREATE OR REPLACE TEMPORARY VIEW gold_eligible_txns_src AS {sql}"
        )
        self._databricks_merge(
            spark,
            src_view="gold_eligible_txns_src",
            target_table=f"{cat}.{s_gold}.gold_dispute_eligible_transactions",
            merge_on="target.transaction_id = source.transaction_id",
        )

    def _databricks_build_cases_summary(
        self, spark: object, cat: str, s_silver: str, s_gold: str
    ) -> None:
        from pyspark.sql import SparkSession  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        silver_prefix = f"{cat}.{s_silver}."
        sql = gold_cases_summary_sql(silver_prefix=silver_prefix, engine="databricks")
        spark.sql(
            f"CREATE OR REPLACE TEMPORARY VIEW gold_cases_summary_src AS {sql}"
        )
        self._databricks_merge(
            spark,
            src_view="gold_cases_summary_src",
            target_table=f"{cat}.{s_gold}.gold_dispute_cases_summary",
            merge_on="target.complaint_id = source.complaint_id",
        )
