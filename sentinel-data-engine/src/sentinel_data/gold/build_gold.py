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

Tables built
------------
gold_dispute_customer_360
    One row per customer_id.  Pre-joins customers, products (aggregated),
    complaints (aggregated) and satisfaction surveys (average CSAT).
    Derived columns: dispute_risk_level, is_repeat_complainer,
    total_active_disputes, avg_sentiment_score.

gold_dispute_eligible_transactions
    One row per transaction_id.  Pre-joins transactions with customers and
    the complaints table.  Derived boolean flags: is_disputed,
    is_eligible_for_dispute (NOT already disputed AND <= 90 days old),
    days_since_transaction.

gold_dispute_cases_summary
    One row per complaint_id.  Pre-joins complaints with customers,
    products, service_agents and call_center_interactions (most recent
    interaction per complaint).  Denormalizes SLA status, agent details,
    and origin interaction sentiment.

Execution engines
-----------------
Local mode      : DuckDB (delta extension), reads ./data/silver/<table>/
                  and writes ./data/gold/<table>/ with OVERWRITE semantics.
Databricks mode : PySpark + Delta MERGE on Unity Catalog managed tables.
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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DISPUTE_ELIGIBILITY_DAYS = 90  # business rule: max days for dispute intake


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
    Build all three Gold serving tables for the Dispute Intake use case.

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
        con.execute(f"SET VARIABLE eligibility_days = {_DISPUTE_ELIGIBILITY_DAYS};")

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

        Aggregates
        ----------
        - products     : product count, total current balance, active product count
        - complaints   : active disputes, total disputes, repeat complainer flag,
                         total compensation paid
        - surveys      : average CSAT (main_score), avg sentiment from interactions

        Derived
        -------
        dispute_risk_level : HIGH  (>= 3 active disputes or is_repeat_complainer)
                             MEDIUM (1-2 active disputes)
                             LOW    (no active disputes)
        """
        out_path = str(gold / "gold_dispute_customer_360")
        arrow_table: pa.Table = con.execute(
            """
            WITH product_agg AS (
                    SELECT
                        customer_id,
                        COUNT(*)                                            AS total_products,
                        COUNT(*) FILTER (WHERE product_status = 'ACTIVE')  AS active_products,
                        SUM(current_balance)                               AS total_balance,
                        MAX(product_type)                                  AS primary_product_type
                    FROM silver_products
                    GROUP BY customer_id
                ),
                complaint_agg AS (
                    SELECT
                        customer_id,
                        COUNT(*)                                            AS total_complaints,
                        COUNT(*) FILTER (WHERE status NOT IN ('CLOSED', 'RESOLVED'))
                                                                           AS active_disputes,
                        BOOL_OR(is_repeat_complainer)                      AS is_repeat_complainer,
                        SUM(COALESCE(compensation_amount, 0))              AS total_compensation_paid
                    FROM silver_complaints
                    GROUP BY customer_id
                ),
                survey_agg AS (
                    SELECT
                        customer_id,
                        AVG(main_score)     AS avg_csat_score,
                        COUNT(*)            AS total_surveys
                    FROM silver_satisfaction_surveys
                    GROUP BY customer_id
                )
                SELECT
                    c.customer_id,
                    c.first_name,
                    c.last_name,
                    c.document_type,
                    c.document_number,
                    c.date_of_birth,
                    c.city,
                    c.state,
                    c.country,
                    c.segment,
                    c.customer_status,
                    c.registration_date,
                    c.credit_score,
                    -- Product aggregates
                    COALESCE(pa.total_products,    0)     AS total_products,
                    COALESCE(pa.active_products,   0)     AS active_products,
                    COALESCE(pa.total_balance,     0.0)   AS total_balance,
                    pa.primary_product_type,
                    -- Complaint aggregates
                    COALESCE(ca.total_complaints,        0)     AS total_complaints,
                    COALESCE(ca.active_disputes,         0)     AS active_disputes,
                    COALESCE(ca.is_repeat_complainer,    FALSE) AS is_repeat_complainer,
                    COALESCE(ca.total_compensation_paid, 0.0)   AS total_compensation_paid,
                    -- Survey aggregates
                    COALESCE(sa.avg_csat_score,  NULL)    AS avg_csat_score,
                    COALESCE(sa.total_surveys,   0)       AS total_surveys,
                    -- Derived risk level
                    CASE
                        WHEN COALESCE(ca.active_disputes, 0) >= 3
                             OR COALESCE(ca.is_repeat_complainer, FALSE) = TRUE
                            THEN 'HIGH'
                        WHEN COALESCE(ca.active_disputes, 0) BETWEEN 1 AND 2
                            THEN 'MEDIUM'
                        ELSE 'LOW'
                    END AS dispute_risk_level,
                    -- Snapshot metadata
                    CURRENT_DATE AS snapshot_date
                FROM silver_customers c
                LEFT JOIN product_agg  pa ON pa.customer_id  = c.customer_id
                LEFT JOIN complaint_agg ca ON ca.customer_id = c.customer_id
                LEFT JOIN survey_agg   sa ON sa.customer_id  = c.customer_id
            """
        ).to_arrow_table()
        write_deltalake(out_path, arrow_table, mode="overwrite")
        logger.info("Built gold_dispute_customer_360 → %s", out_path)

    def _local_build_eligible_transactions(
        self, con: duckdb.DuckDBPyConnection, gold: Path
    ) -> None:
        """
        Build gold_dispute_eligible_transactions (1 row per transaction_id).

        Derived flags
        -------------
        is_disputed              : True when an open complaint references this transaction
        days_since_transaction   : CURRENT_DATE − transaction_date
        is_eligible_for_dispute  : NOT is_disputed AND days_since_transaction <= 90
        """
        out_path = str(gold / "gold_dispute_eligible_transactions")
        eligible_arrow: pa.Table = con.execute(
            f"""
            WITH disputed_txns AS (
                SELECT DISTINCT referenced_transaction_id AS transaction_id
                FROM silver_complaints
                WHERE referenced_transaction_id IS NOT NULL
                  AND status NOT IN ('CLOSED', 'RESOLVED')
            )
            SELECT
                t.transaction_id,
                t.transaction_date,
                t.process_date,
                t.product_id,
                t.customer_id,
                t.transaction_type,
                CAST(t.amount AS DOUBLE)      AS amount,
                t.currency,
                t.channel,
                t.transaction_country,
                t.transaction_status,
                t.is_fraud,
                CAST(t.fraud_score AS DOUBLE) AS fraud_score,
                t.merchant_name,
                t.merchant_category,
                -- Customer context
                c.first_name          AS customer_first_name,
                c.last_name           AS customer_last_name,
                c.segment             AS customer_segment,
                c.country             AS customer_country,
                c.credit_score        AS customer_credit_score,
                -- Derived flags
                (dt.transaction_id IS NOT NULL)                        AS is_disputed,
                DATE_DIFF('day', t.transaction_date::DATE, CURRENT_DATE) AS days_since_transaction,
                (
                    dt.transaction_id IS NULL
                    AND DATE_DIFF('day', t.transaction_date::DATE, CURRENT_DATE)
                        <= {_DISPUTE_ELIGIBILITY_DAYS}
                )                                                       AS is_eligible_for_dispute,
                -- Snapshot metadata
                CURRENT_DATE AS snapshot_date
            FROM silver_transactions t
            LEFT JOIN silver_customers  c  ON c.customer_id    = t.customer_id
            LEFT JOIN disputed_txns     dt ON dt.transaction_id = t.transaction_id
            """
        ).to_arrow_table()
        write_deltalake(out_path, eligible_arrow, mode="overwrite")
        logger.info("Built gold_dispute_eligible_transactions → %s", out_path)

    def _local_build_service_eligible_transactions(
        self, con: duckdb.DuckDBPyConnection, gold: Path
    ) -> None:
        """
        Build v_service_dispute_eligible_transactions (PII-free service projection).

        Derived from gold_dispute_eligible_transactions by dropping the three PII
        columns mandated by ADR 008:
            - customer_first_name
            - customer_last_name
            - customer_credit_score

        This table is the surface exposed to the FastAPI backend and any downstream
        service that does not hold explicit PII-READ permission.  All eligibility
        flags and transaction fields are preserved.
        """
        out_path = str(gold / "v_service_dispute_eligible_transactions")
        gold_src = str(gold / "gold_dispute_eligible_transactions")

        if not Path(gold_src).exists() or not any(Path(gold_src).iterdir()):
            logger.warning(
                "gold_dispute_eligible_transactions not found – "
                "skipping service view build: %s",
                gold_src,
            )
            return

        service_arrow: pa.Table = con.execute(
            f"""
            SELECT
                transaction_id,
                transaction_date,
                process_date,
                product_id,
                customer_id,
                transaction_type,
                CAST(amount AS DOUBLE)      AS amount,
                currency,
                channel,
                transaction_country,
                transaction_status,
                is_fraud,
                CAST(fraud_score AS DOUBLE) AS fraud_score,
                merchant_name,
                merchant_category,
                -- Customer context (PII-safe subset only)
                customer_segment,
                customer_country,
                -- Eligibility flags
                is_disputed,
                days_since_transaction,
                is_eligible_for_dispute,
                -- Snapshot metadata
                snapshot_date
            FROM delta_scan('{gold_src}')
            """
        ).to_arrow_table()
        write_deltalake(out_path, service_arrow, mode="overwrite")
        logger.info("Built v_service_dispute_eligible_transactions → %s", out_path)

    def _local_build_cases_summary(
        self, con: duckdb.DuckDBPyConnection, gold: Path
    ) -> None:
        """
        Build gold_dispute_cases_summary (1 row per complaint_id).

        Denormalizes
        ------------
        - complaints  : full case lifecycle data + SLA breach flag
        - customers   : name, segment, contact info
        - products    : product type, number, currency
        - service_agents : assigned agent name, type, experience level
        - call_center_interactions : most recent interaction sentiment for the case

        The most recent call center interaction is resolved via ROW_NUMBER OVER
        (PARTITION BY complaint_id ORDER BY interaction_date DESC).
        """
        out_path = str(gold / "gold_dispute_cases_summary")
        cases_arrow: pa.Table = con.execute(
            """
            WITH latest_interaction AS (
                    SELECT * EXCLUDE (rn)
                    FROM (
                        SELECT
                            cci.*,
                            ROW_NUMBER() OVER (
                                PARTITION BY cci.complaint_id
                                ORDER BY cci.interaction_date DESC
                            ) AS rn
                        FROM silver_call_center_interactions cci
                        WHERE cci.complaint_id IS NOT NULL
                    )
                    WHERE rn = 1
                )
                SELECT
                    -- Complaint core
                    comp.complaint_id,
                    comp.creation_date,
                    comp.resolution_date,
                    comp.case_type,
                    comp.category,
                    comp.subcategory,
                    comp.reception_channel,
                    comp.description,
                    comp.priority,
                    comp.status,
                    comp.sla_breached,
                    comp.resolution_notes,
                    comp.compensation_amount,
                    comp.referenced_transaction_id,
                    comp.is_repeat_complainer,
                    -- Customer context
                    comp.customer_id,
                    c.first_name              AS customer_first_name,
                    c.last_name               AS customer_last_name,
                    c.segment                 AS customer_segment,
                    c.country                 AS customer_country,
                    c.credit_score            AS customer_credit_score,
                    -- Product context
                    comp.product_id,
                    p.product_type,
                    p.product_number,
                    p.currency                AS product_currency,
                    p.current_balance         AS product_balance,
                    -- Assigned agent context
                    comp.assigned_agent_id,
                    sa.first_name             AS agent_first_name,
                    sa.last_name              AS agent_last_name,
                    sa.agent_type,
                    sa.experience_level       AS agent_experience_level,
                    sa.languages              AS agent_languages,
                    -- Origin interaction context (most recent)
                    li.interaction_id         AS origin_interaction_id,
                    li.interaction_date        AS origin_interaction_date,
                    li.channel                AS origin_channel,
                    li.contact_reason         AS origin_contact_reason,
                    li.sentiment_score        AS origin_sentiment_score,
                    li.was_escalated          AS origin_was_escalated,
                    -- SLA days calculation
                    DATE_DIFF(
                        'day', comp.creation_date::DATE,
                        COALESCE(comp.resolution_date::DATE, CURRENT_DATE)
                    )                         AS case_age_days,
                    -- Snapshot metadata
                    CURRENT_DATE AS snapshot_date
                FROM silver_complaints comp
                LEFT JOIN silver_customers         c  ON c.customer_id      = comp.customer_id
                LEFT JOIN silver_products          p  ON p.product_id       = comp.product_id
                LEFT JOIN silver_service_agents    sa ON sa.agent_id        = comp.assigned_agent_id
                LEFT JOIN latest_interaction       li ON li.complaint_id    = comp.complaint_id
            """
        ).to_arrow_table()
        write_deltalake(out_path, cases_arrow, mode="overwrite")
        logger.info("Built gold_dispute_cases_summary → %s", out_path)

    # ------------------------------------------------------------------
    # Cloud mode – PySpark + Delta MERGE
    # ------------------------------------------------------------------

    def _run_databricks(self, spark: object) -> None:
        """
        Build all Gold tables on Databricks using PySpark SQL and Delta MERGE.

        Each Gold table is materialized as a PySpark temporary view (built via
        spark.sql) then MERGE'd into the target Unity Catalog Delta table on its
        primary key.  This guarantees idempotency: re-running the job never
        produces duplicate rows.
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
        """
        MERGE *src_view* rows into *target_table* on *merge_on* condition.

        Creates the table from the view when it does not yet exist.
        """
        from pyspark.sql import SparkSession  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        if not spark.catalog.tableExists(target_table):
            spark.sql(
                f"CREATE TABLE {target_table} AS SELECT * FROM {src_view}"
            )
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
        """PySpark equivalent of _local_build_customer_360."""
        from pyspark.sql import SparkSession  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        spark.sql(
            f"""
            CREATE OR REPLACE TEMPORARY VIEW gold_customer_360_src AS
            WITH product_agg AS (
                SELECT
                    customer_id,
                    COUNT(*)                                           AS total_products,
                    COUNT(*) FILTER (WHERE product_status = 'ACTIVE') AS active_products,
                    SUM(current_balance)                              AS total_balance,
                    MAX(product_type)                                 AS primary_product_type
                FROM {cat}.{s_silver}.products
                GROUP BY customer_id
            ),
            complaint_agg AS (
                SELECT
                    customer_id,
                    COUNT(*)                                                       AS total_complaints,
                    COUNT(*) FILTER (WHERE status NOT IN ('CLOSED', 'RESOLVED'))  AS active_disputes,
                    BOOL_OR(is_repeat_complainer)                                 AS is_repeat_complainer,
                    SUM(COALESCE(compensation_amount, 0))                         AS total_compensation_paid
                FROM {cat}.{s_silver}.complaints
                GROUP BY customer_id
            ),
            survey_agg AS (
                SELECT
                    customer_id,
                    AVG(main_score)  AS avg_csat_score,
                    COUNT(*)         AS total_surveys
                FROM {cat}.{s_silver}.satisfaction_surveys
                GROUP BY customer_id
            )
            SELECT
                c.customer_id,
                c.first_name, c.last_name, c.document_type, c.document_number,
                c.date_of_birth, c.city, c.state, c.country, c.segment,
                c.customer_status, c.registration_date, c.credit_score,
                COALESCE(pa.total_products,    0)     AS total_products,
                COALESCE(pa.active_products,   0)     AS active_products,
                COALESCE(pa.total_balance,     0.0)   AS total_balance,
                pa.primary_product_type,
                COALESCE(ca.total_complaints,        0)     AS total_complaints,
                COALESCE(ca.active_disputes,         0)     AS active_disputes,
                COALESCE(ca.is_repeat_complainer,    FALSE) AS is_repeat_complainer,
                COALESCE(ca.total_compensation_paid, 0.0)   AS total_compensation_paid,
                sa.avg_csat_score,
                COALESCE(sa.total_surveys, 0) AS total_surveys,
                CASE
                    WHEN COALESCE(ca.active_disputes, 0) >= 3
                         OR COALESCE(ca.is_repeat_complainer, FALSE)
                        THEN 'HIGH'
                    WHEN COALESCE(ca.active_disputes, 0) BETWEEN 1 AND 2
                        THEN 'MEDIUM'
                    ELSE 'LOW'
                END AS dispute_risk_level,
                CURRENT_DATE AS snapshot_date
            FROM {cat}.{s_silver}.customers c
            LEFT JOIN product_agg   pa ON pa.customer_id  = c.customer_id
            LEFT JOIN complaint_agg ca ON ca.customer_id  = c.customer_id
            LEFT JOIN survey_agg    sa ON sa.customer_id  = c.customer_id
            """
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
        """PySpark equivalent of _local_build_eligible_transactions."""
        from pyspark.sql import SparkSession  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        spark.sql(
            f"""
            CREATE OR REPLACE TEMPORARY VIEW gold_eligible_txns_src AS
            WITH disputed_txns AS (
                SELECT DISTINCT referenced_transaction_id AS transaction_id
                FROM {cat}.{s_silver}.complaints
                WHERE referenced_transaction_id IS NOT NULL
                  AND status NOT IN ('CLOSED', 'RESOLVED')
            )
            SELECT
                t.transaction_id, t.transaction_date, t.process_date,
                t.product_id, t.customer_id, t.transaction_type,
                t.amount, t.currency, t.channel, t.transaction_country,
                t.transaction_status, t.is_fraud, t.fraud_score,
                t.merchant_name, t.merchant_category,
                c.first_name   AS customer_first_name,
                c.last_name    AS customer_last_name,
                c.segment      AS customer_segment,
                c.country      AS customer_country,
                c.credit_score AS customer_credit_score,
                (dt.transaction_id IS NOT NULL)                                AS is_disputed,
                DATEDIFF(CURRENT_DATE, t.transaction_date)                     AS days_since_transaction,
                (
                    dt.transaction_id IS NULL
                    AND DATEDIFF(CURRENT_DATE, t.transaction_date) <= {_DISPUTE_ELIGIBILITY_DAYS}
                )                                                              AS is_eligible_for_dispute,
                CURRENT_DATE AS snapshot_date
            FROM {cat}.{s_silver}.transactions t
            LEFT JOIN {cat}.{s_silver}.customers c  ON c.customer_id    = t.customer_id
            LEFT JOIN disputed_txns              dt ON dt.transaction_id = t.transaction_id
            """
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
        """PySpark equivalent of _local_build_cases_summary."""
        from pyspark.sql import SparkSession  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        spark.sql(
            f"""
            CREATE OR REPLACE TEMPORARY VIEW gold_cases_summary_src AS
            WITH latest_interaction AS (
                SELECT * EXCEPT (rn)
                FROM (
                    SELECT
                        *,
                        ROW_NUMBER() OVER (
                            PARTITION BY complaint_id
                            ORDER BY interaction_date DESC
                        ) AS rn
                    FROM {cat}.{s_silver}.call_center_interactions
                    WHERE complaint_id IS NOT NULL
                )
                WHERE rn = 1
            )
            SELECT
                comp.complaint_id, comp.creation_date, comp.resolution_date,
                comp.case_type, comp.category, comp.subcategory,
                comp.reception_channel, comp.description, comp.priority,
                comp.status, comp.sla_breached, comp.resolution_notes,
                comp.compensation_amount, comp.referenced_transaction_id,
                comp.is_repeat_complainer,
                comp.customer_id,
                c.first_name   AS customer_first_name,
                c.last_name    AS customer_last_name,
                c.segment      AS customer_segment,
                c.country      AS customer_country,
                c.credit_score AS customer_credit_score,
                comp.product_id,
                p.product_type, p.product_number,
                p.currency     AS product_currency,
                p.current_balance AS product_balance,
                comp.assigned_agent_id,
                sa.first_name        AS agent_first_name,
                sa.last_name         AS agent_last_name,
                sa.agent_type,
                sa.experience_level  AS agent_experience_level,
                sa.languages         AS agent_languages,
                li.interaction_id    AS origin_interaction_id,
                li.interaction_date  AS origin_interaction_date,
                li.channel           AS origin_channel,
                li.contact_reason    AS origin_contact_reason,
                li.sentiment_score   AS origin_sentiment_score,
                li.was_escalated     AS origin_was_escalated,
                DATEDIFF(
                    COALESCE(comp.resolution_date, CURRENT_DATE),
                    comp.creation_date
                )                    AS case_age_days,
                CURRENT_DATE AS snapshot_date
            FROM {cat}.{s_silver}.complaints              comp
            LEFT JOIN {cat}.{s_silver}.customers          c  ON c.customer_id   = comp.customer_id
            LEFT JOIN {cat}.{s_silver}.products           p  ON p.product_id    = comp.product_id
            LEFT JOIN {cat}.{s_silver}.service_agents     sa ON sa.agent_id     = comp.assigned_agent_id
            LEFT JOIN latest_interaction                  li ON li.complaint_id = comp.complaint_id
            """
        )
        self._databricks_merge(
            spark,
            src_view="gold_cases_summary_src",
            target_table=f"{cat}.{s_gold}.gold_dispute_cases_summary",
            merge_on="target.complaint_id = source.complaint_id",
        )
