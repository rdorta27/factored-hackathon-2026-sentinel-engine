"""
Silver layer transformer – validation, quarantine split, deduplication, Delta MERGE.

Pipeline (per table)
--------------------
1. Read the Bronze Delta table (local path or Databricks table).
2. Validate every row against the quality rules defined in ``sentinel_data.catalog``
   for the target table.  Rules encode all NOT NULL constraints and domain invariants
   declared in the LATAM Bank data dictionary (13 tables).
3. Split into two DataFrames:
       clean_df      - rows that pass all checks
       quarantine_df - rows that fail at least one check
4. Deduplicate clean_df using a window function:
       ROW_NUMBER() OVER (PARTITION BY <pk>[, <pk2>] ORDER BY _ingested_at DESC, _source_file DESC)
       Composite primary keys (e.g. daily_exchange_rates) are supported.
5. MERGE clean_df into the Silver Delta table on the full primary key.
6. Append quarantine_df to the rejected_records Delta table.

Execution engines
-----------------
Local mode      : DuckDB (delta extension)
Databricks mode : PySpark + delta-spark

Quarantine record schema
------------------------
    raw_record       - original row serialized to JSON
    rejection_reason - semicolon-separated list of failed rule names
    rejected_at      - ISO 8601 UTC timestamp
    source_file      - value from the _source_file audit column
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import duckdb
import pyarrow as pa
from deltalake import write_deltalake
from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel_data.catalog import QualityRule, RunMode, TableDefinition, get_table

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class SilverTransformerConfig(BaseModel):
    """Runtime parameters for a single Silver transformation run."""

    table_name: str = Field(
        ..., description="Must match a key in sentinel_data.catalog.TABLE_REGISTRY"
    )
    run_mode: RunMode = Field(RunMode.LOCAL)

    # When left empty, primary_keys and quality_rules are resolved from the catalog.
    # Explicit values override the catalog (useful for unit tests or one-off overrides).
    primary_keys: list[str] = Field(
        default_factory=list,
        description="Override catalog primary keys (leave empty to use catalog)",
    )
    quality_rules: list[QualityRule] = Field(
        default_factory=list,
        description="Override catalog quality rules (leave empty to use catalog)",
    )

    # Local paths
    local_bronze_dir: Path = Field(Path("data/bronze"))
    local_silver_dir: Path = Field(Path("data/silver"))

    # Databricks / Unity Catalog
    databricks_catalog: str = Field("sentinel")
    databricks_schema_bronze: str = Field("bronze")
    databricks_schema_silver: str = Field("silver")
    quarantine_table: str = Field("rejected_records")

    model_config = ConfigDict(use_enum_values=True)

    @model_validator(mode="after")
    def _resolve_catalog_defaults(self) -> "SilverTransformerConfig":
        """
        Populate primary_keys and quality_rules from the catalog when not
        explicitly provided.  Raises ``KeyError`` if table_name is unknown.
        """
        defn: TableDefinition = get_table(self.table_name)
        if not self.primary_keys:
            self.primary_keys = defn.primary_keys
        if not self.quality_rules:
            self.quality_rules = defn.quality_rules
        return self


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------


class SilverTransformer:
    """
    Validate, quarantine, deduplicate, and MERGE Bronze records into Silver.

    Quality rules and primary keys are resolved automatically from the LATAM
    Bank catalog (``sentinel_data.catalog``) for all 13 registered tables.
    Composite primary keys (e.g. ``daily_exchange_rates``) are handled
    transparently in both the deduplication window and the MERGE condition.

    Parameters
    ----------
    config : SilverTransformerConfig
        Runtime configuration.  ``table_name`` is validated against the catalog.

    Examples
    --------
    Local run (catalog rules applied automatically)::

        cfg = SilverTransformerConfig(table_name="transactions")
        SilverTransformer(cfg).run()

    Databricks run::

        cfg = SilverTransformerConfig(
            table_name="transactions",
            run_mode=RunMode.DATABRICKS,
        )
        SilverTransformer(cfg).run(spark=spark)
    """

    def __init__(self, config: SilverTransformerConfig) -> None:
        self.cfg = config
        self._table_def: TableDefinition = get_table(config.table_name)
        self._rejected_at: str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, spark: Optional[object] = None) -> None:
        """Dispatch to the appropriate engine based on run_mode."""
        logger.info(
            "Silver transformation started | table=%s pk=%s rules=%d mode=%s",
            self.cfg.table_name,
            self.cfg.primary_keys,
            len(self.cfg.quality_rules),
            self.cfg.run_mode,
        )
        if self.cfg.run_mode == RunMode.LOCAL:
            self._run_local()
        else:
            if spark is None:
                raise ValueError("A SparkSession is required in DATABRICKS run mode.")
            self._run_databricks(spark)

    # ------------------------------------------------------------------
    # Local mode – DuckDB -> Delta
    # ------------------------------------------------------------------

    def _run_local(self) -> None:
        """
        Execute the full pipeline with DuckDB.

        Steps
        -----
        1. Read Bronze Delta table into a DuckDB in-memory view.
        2. Apply catalog quality rules to tag each row.
        3. Write failing rows to data/silver/rejected_records/.
        4. Deduplicate passing rows with ROW_NUMBER() on the composite PK.
        5. MERGE deduplicated rows into data/silver/<table>/.
        """
        bronze_path = str((self.cfg.local_bronze_dir / self.cfg.table_name).resolve())
        silver_path = str((self.cfg.local_silver_dir / self.cfg.table_name).resolve())
        quarantine_path = str((self.cfg.local_silver_dir / self.cfg.quarantine_table).resolve())

        Path(silver_path).mkdir(parents=True, exist_ok=True)
        Path(quarantine_path).mkdir(parents=True, exist_ok=True)

        con = duckdb.connect()
        con.execute("INSTALL delta; LOAD delta;")

        # Step 1 – load Bronze into an in-memory view
        con.execute(
            f"CREATE OR REPLACE VIEW bronze_raw AS SELECT * FROM delta_scan('{bronze_path}');"
        )

        # Step 1b – apply country standardisation before validation.
        # Raw Bronze contains "Mexico" (no accent, ~3.4 k rows) alongside the
        # canonical "México".  Normalise here so Silver is 100 % clean.
        normalization_sql = self._build_country_normalization_sql(con)
        con.execute(
            f"""
            CREATE OR REPLACE VIEW bronze_normalized AS
            SELECT {normalization_sql}
            FROM bronze_raw;
            """
        )

        # Step 2 – validate rows and compute rejection_reason per row
        validation_sql = self._build_validation_sql()
        con.execute(
            f"""
            CREATE OR REPLACE VIEW validated AS
            SELECT
                *,
                {validation_sql} AS rejection_reason
            FROM bronze_normalized;
            """
        )

        # Step 3 – write quarantine rows
        # Build STRUCT_PACK with explicit column aliases (STRUCT_PACK(* EXCLUDE …)
        # is not supported in DuckDB 1.1.x).
        rejected_at = self._rejected_at
        all_cols = [
            desc[0]
            for desc in con.execute("SELECT * FROM validated LIMIT 0").description
        ]
        business_cols = [c for c in all_cols if c != "rejection_reason"]
        struct_args = ", ".join(f'"{c}" := "{c}"' for c in business_cols)
        quarantine_arrow: pa.Table = con.execute(
            f"""
            SELECT
                TO_JSON(STRUCT_PACK({struct_args})) AS raw_record,
                rejection_reason,
                '{rejected_at}'   AS rejected_at,
                _source_file      AS source_file
            FROM validated
            WHERE rejection_reason != ''
            """
        ).to_arrow_table()
        if quarantine_arrow.num_rows > 0:
            write_deltalake(quarantine_path, quarantine_arrow, mode="append")

        # Step 4 – deduplicate clean rows on composite PK
        # Use the config's primary_keys (may differ from catalog when overridden in tests).
        partition_keys = ", ".join(self.cfg.primary_keys)
        con.execute(
            f"""
            CREATE OR REPLACE VIEW deduplicated AS
            SELECT * EXCLUDE (rn)
            FROM (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY {partition_keys}
                        ORDER BY _ingested_at DESC, _source_file DESC
                    ) AS rn
                FROM validated
                WHERE rejection_reason = ''
            )
            WHERE rn = 1;
            """
        )

        # Step 5 – MERGE into Silver Delta table
        # DuckDB delta extension approximates MERGE by unioning with existing
        # Silver rows, re-deduplicating on the PK, then overwriting.
        silver_exists = Path(silver_path).exists() and any(Path(silver_path).iterdir())
        if silver_exists:
            con.execute(
                f"""
                CREATE OR REPLACE VIEW merged AS
                SELECT * EXCLUDE (rn)
                FROM (
                    SELECT
                        *,
                        ROW_NUMBER() OVER (
                            PARTITION BY {partition_keys}
                            ORDER BY _ingested_at DESC, _source_file DESC
                        ) AS rn
                    FROM (
                        SELECT * FROM delta_scan('{silver_path}')
                        UNION ALL
                        SELECT * FROM deduplicated
                    )
                )
                WHERE rn = 1;
                """
            )
            source_view = "merged"
        else:
            source_view = "deduplicated"

        silver_arrow: pa.Table = con.execute(f"SELECT * FROM {source_view}").to_arrow_table()
        write_deltalake(silver_path, silver_arrow, mode="overwrite")

        con.close()
        logger.info(
            "Silver local transformation complete | table=%s silver=%s quarantine=%s",
            self.cfg.table_name,
            silver_path,
            quarantine_path,
        )

    def _build_country_normalization_sql(self, con: duckdb.DuckDBPyConnection) -> str:
        """
        Return a SELECT column list that standardises country values.

        The raw Bronze dataset contains "Mexico" (without accent) alongside the
        canonical "México".  This method replaces the relevant country column(s)
        with an explicit CASE expression so all downstream Silver tables carry
        only the canonical spelling.

        Affected tables / columns
        -------------------------
        customers    : country
        transactions : transaction_country
        """
        all_cols = [
            desc[0]
            for desc in con.execute("SELECT * FROM bronze_raw LIMIT 0").description
        ]

        _MEXICO_FIX = "CASE WHEN {col} = 'Mexico' THEN 'México' ELSE {col} END AS {col}"

        country_cols = {"country", "transaction_country"}
        parts = []
        for col in all_cols:
            if col in country_cols:
                parts.append(_MEXICO_FIX.format(col=col))
            else:
                parts.append(f'"{col}"')
        return ", ".join(parts)

    def _build_validation_sql(self) -> str:
        """
        Build a SQL expression that produces a semicolon-separated string of
        failed rule names for each row, or an empty string when all rules pass.

        Each rule contributes its name when the row fails its predicate,
        otherwise contributes an empty string.  The fragments are concatenated
        with '||' and leading/trailing semicolons are stripped.

        Example output for two rules::

            TRIM(BOTH ';' FROM (
                CASE WHEN NOT (transaction_id IS NOT NULL)
                     THEN 'transaction_id_not_null' ELSE '' END
                || ';' ||
                CASE WHEN NOT (amount IS NOT NULL)
                     THEN 'amount_not_null' ELSE '' END
            ))
        """
        if not self.cfg.quality_rules:
            # No rules configured – every row is considered clean.
            return "''"

        fragments = " || ';' || ".join(
            f"CASE WHEN NOT ({r.sql_predicate}) THEN '{r.rule_name}' ELSE '' END"
            for r in self.cfg.quality_rules
        )
        return f"TRIM(BOTH ';' FROM ({fragments}))"

    # ------------------------------------------------------------------
    # Cloud mode – PySpark + Delta Lake MERGE
    # ------------------------------------------------------------------

    def _run_databricks(self, spark: object) -> None:
        """
        Execute the full pipeline with PySpark on Databricks.

        Steps
        -----
        1. Read Bronze Delta table from Unity Catalog.
        2. Validate rows using catalog quality rules as PySpark Column expressions.
        3. Split into clean_df and quarantine_df.
        4. Append quarantine_df to the rejected_records managed table.
        5. Deduplicate clean_df with Window on the composite PK.
        6. Delta MERGE clean_df into the Silver table using the full PK condition.
        """
        from delta.tables import DeltaTable  # type: ignore[import]
        from pyspark.sql import SparkSession, Window  # type: ignore[import]
        from pyspark.sql import functions as F  # type: ignore[import]
        from pyspark.sql.types import StringType  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        catalog = self.cfg.databricks_catalog
        schema_bronze = self.cfg.databricks_schema_bronze
        schema_silver = self.cfg.databricks_schema_silver
        table_name = self.cfg.table_name

        bronze_table = f"{catalog}.{schema_bronze}.{table_name}"
        silver_table = f"{catalog}.{schema_silver}.{table_name}"
        quarantine_table_fqn = f"{catalog}.{schema_silver}.{self.cfg.quarantine_table}"

        logger.info(
            "Reading Bronze table: %s | pk=%s | rules=%d",
            bronze_table,
            self.cfg.primary_keys,
            len(self.cfg.quality_rules),
        )
        df = spark.table(bronze_table)

        # Step 2 – build a rejection_reason column from catalog rules
        rule_conditions = [
            F.when(~F.expr(rule.sql_predicate), F.lit(rule.rule_name)).otherwise(F.lit(""))
            for rule in self.cfg.quality_rules
        ]
        rejection_expr = (
            F.concat_ws(";", *[F.when(c != "", c) for c in rule_conditions])
            if rule_conditions
            else F.lit("")
        )
        validated_df = df.withColumn("rejection_reason", rejection_expr)

        # Step 3 – split clean vs. quarantine
        clean_df = validated_df.filter(F.col("rejection_reason") == "").drop("rejection_reason")
        quarantine_df = validated_df.filter(F.col("rejection_reason") != "")

        # Step 4 – append quarantined rows
        @F.udf(returnType=StringType())  # type: ignore[misc]
        def row_to_json(row: Any) -> str:
            return json.dumps(row.asDict(), default=str)

        rejected_at = self._rejected_at
        quarantine_out = quarantine_df.select(
            row_to_json(F.struct([c for c in df.columns])).alias("raw_record"),
            F.col("rejection_reason"),
            F.lit(rejected_at).cast("timestamp").alias("rejected_at"),
            F.col("_source_file").alias("source_file"),
        )
        quarantine_out.write.format("delta").mode("append").saveAsTable(quarantine_table_fqn)
        logger.info("Quarantine records written to: %s", quarantine_table_fqn)

        # Step 5 – deduplicate on composite PK
        window_spec = Window.partitionBy(*self.cfg.primary_keys).orderBy(
            F.col("_ingested_at").desc(),
            F.col("_source_file").desc(),
        )
        deduped_df = (
            clean_df.withColumn("_rn", F.row_number().over(window_spec))
            .filter(F.col("_rn") == 1)
            .drop("_rn")
        )

        # Step 6 – MERGE into Silver using full PK condition from catalog
        merge_condition = self._table_def.merge_condition
        if spark.catalog.tableExists(silver_table):
            silver_delta = DeltaTable.forName(spark, silver_table)
            (
                silver_delta.alias("target")
                .merge(deduped_df.alias("source"), merge_condition)
                .whenMatchedUpdateAll()
                .whenNotMatchedInsertAll()
                .execute()
            )
        else:
            deduped_df.write.format("delta").mode("overwrite").saveAsTable(silver_table)

        logger.info(
            "Silver Databricks transformation complete | table=%s merge_on='%s'",
            silver_table,
            merge_condition,
        )
