"""
Bronze layer ingestor – dual-mode (local DuckDB + Databricks PySpark).

Responsibility
--------------
Append raw CSV records to the Bronze Delta layer without any transformation.
Every row receives four immutable audit columns:

    _source_system  – logical name of the originating system (e.g. "s3", "local")
    _source_file    – absolute path or S3 URI of the originating file
    _ingested_at    – ISO 8601 UTC timestamp of the ingestion run
    _batch_id       – UUID that groups all files processed in a single run

Table registry
--------------
All 13 source tables are declared in ``sentinel_data.catalog``.  The ingestor
validates the requested table name against that registry and uses the
``TableDefinition`` to:
  - Log the primary key(s) for observability.
  - Build the correct S3 prefix path that matches the table's partition strategy:
      daily             → s3://<bucket>/<table>/year=YYYY/month=MM/day=DD/
      monthly_snapshot  → s3://<bucket>/<table>/year=YYYY/month=MM/
      full_snapshot     → s3://<bucket>/<table>/

Idempotency guarantees
----------------------
Local mode  : Before appending a file the existing Bronze Delta table is queried
              for its distinct ``_source_file`` values.  Files whose resolved
              absolute path already appears there are skipped silently.

Cloud mode  : Auto Loader persists a per-table checkpoint at
              ``<checkpoint_base>/<table_name>/``.  The checkpoint tracks every
              committed S3 object so re-triggering the job never re-processes
              already-ingested files.

Local mode  : DuckDB (delta extension) reads ./data/raw/<table>/ → ./data/bronze/<table>/
Cloud mode  : PySpark Auto Loader reads s3://<bucket>/<table>/ → Databricks Delta table
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import duckdb
import pyarrow as pa
from deltalake import write_deltalake
from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentinel_data.catalog import PartitionStrategy, RunMode, TableDefinition, get_table

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class BronzeIngestorConfig(BaseModel):
    """Runtime parameters for a single Bronze ingestion run."""

    table_name: str = Field(..., description="Must match a key in sentinel_data.catalog.TABLE_REGISTRY")
    source_system: str = Field("s3", description="Label written to _source_system column")
    run_mode: RunMode = Field(RunMode.LOCAL)

    # Local paths
    local_raw_dir: Path = Field(Path("data/raw"))
    local_bronze_dir: Path = Field(Path("data/bronze"))

    # Cloud / Databricks
    s3_bucket: str = Field("")
    s3_prefix: str = Field("", description="Optional key prefix inside the S3 bucket")
    databricks_catalog: str = Field("sentinel")
    databricks_schema: str = Field("bronze")
    checkpoint_base: str = Field("/Volumes/sentinel/bronze/_checkpoints")

    # Optional date filter for daily-partitioned tables (cloud mode).
    # When set, Auto Loader loads only that single partition prefix.
    # Format: YYYY-MM-DD.  If empty, all available partitions are discovered.
    partition_date: str = Field(
        "",
        description="ISO date (YYYY-MM-DD) to scope S3 ingestion to one daily partition",
    )

    model_config = ConfigDict(use_enum_values=True)

    @model_validator(mode="after")
    def _validate_table_name(self) -> "BronzeIngestorConfig":
        """Raise early if the table is not in the catalog."""
        get_table(self.table_name)  # raises KeyError with a helpful message if unknown
        return self


# ---------------------------------------------------------------------------
# Ingestor
# ---------------------------------------------------------------------------


class BronzeIngestor:
    """
    Append-only ingestor that lands raw records into the Bronze Delta layer.

    The table definition is resolved from the central catalog at construction
    time and used for logging, S3 path construction, and idempotency checks.

    Parameters
    ----------
    config : BronzeIngestorConfig
        Runtime configuration.  ``table_name`` is validated against
        ``sentinel_data.catalog.TABLE_REGISTRY``.

    Examples
    --------
    Local run::

        cfg = BronzeIngestorConfig(table_name="transactions")
        BronzeIngestor(cfg).run()

    Databricks run (from a Job task)::

        cfg = BronzeIngestorConfig(
            table_name="transactions",
            run_mode=RunMode.DATABRICKS,
            s3_bucket="<bucket-name-from-env>",
            partition_date="2026-01-15",
        )
        BronzeIngestor(cfg).run(spark=spark)
    """

    def __init__(self, config: BronzeIngestorConfig) -> None:
        self.cfg = config
        self._table_def: TableDefinition = get_table(config.table_name)
        self._ingested_at: str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._batch_id: str = str(uuid.uuid4())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, spark: Optional[object] = None) -> None:
        """Dispatch to DuckDB (local) or PySpark (Databricks) engine."""
        logger.info(
            "Bronze ingestion started | table=%s pk=%s mode=%s batch_id=%s ts=%s",
            self.cfg.table_name,
            self._table_def.primary_keys,
            self.cfg.run_mode,
            self._batch_id,
            self._ingested_at,
        )
        if self.cfg.run_mode == RunMode.LOCAL:
            self._run_local()
        else:
            if spark is None:
                raise ValueError("A SparkSession is required in DATABRICKS run mode.")
            self._run_databricks(spark)

    # ------------------------------------------------------------------
    # Local mode – DuckDB → Delta
    # ------------------------------------------------------------------

    def _already_ingested_files(
        self, con: duckdb.DuckDBPyConnection, delta_path: str
    ) -> set[str]:
        """
        Return the set of ``_source_file`` values already committed to the
        Bronze Delta table at *delta_path*.

        Returns an empty set when the table does not yet exist so that first-run
        behaviour is identical to subsequent runs.
        """
        if not Path(delta_path).exists() or not any(Path(delta_path).iterdir()):
            return set()
        try:
            rows = con.execute(
                f"SELECT DISTINCT _source_file FROM delta_scan('{delta_path}')"
            ).fetchall()
            return {row[0] for row in rows if row[0] is not None}
        except Exception as exc:  # noqa: BLE001
            # Partially-written or corrupt table – treat as no history.
            logger.warning(
                "Could not read existing Bronze table at %s (%s) – treating as empty.",
                delta_path,
                exc,
            )
            return set()

    def _resolve_local_csv_files(self) -> list[Path]:
        """
        Locate all CSV files for this table under local_raw_dir.

        Discovery order (first match wins):
        1. Sub-directory ``<raw_dir>/<table>/``       → ``**/*.csv``
        2. Flat file ``<raw_dir>/<table>.csv``
        3. Sub-directory ``<raw_dir>/data/<table>/``  → ``**/*.csv``
        4. Flat file ``<raw_dir>/data/<table>.csv``

        Matching is case-insensitive on directory/file names.
        """
        table = self.cfg.table_name
        raw_dir = self.cfg.local_raw_dir
        search_roots: list[Path] = [raw_dir]
        nested = raw_dir / "data"
        if nested.is_dir():
            search_roots.append(nested)

        for root in search_roots:
            try:
                entries = {p.name.lower(): p for p in root.iterdir()}
            except PermissionError:
                continue

            # Sub-directory
            subdir = entries.get(table.lower())
            if subdir and subdir.is_dir():
                files = sorted(subdir.rglob("*.csv"))
                if files:
                    return files

            # Flat file
            flat = entries.get(f"{table.lower()}.csv")
            if flat and flat.is_file():
                return [flat]

        return []

    def _run_local(self) -> None:
        """
        Read all CSV files for this table (flat or Hive-partitioned) and append
        only previously unseen files to the Bronze Delta table.

        Idempotency
        -----------
        The resolved absolute path of every candidate CSV is checked against the
        set of ``_source_file`` values already present in the Bronze table.
        Files already recorded are skipped without touching the Delta table.

        Requires DuckDB >= 0.10 with the delta extension:
            INSTALL delta; LOAD delta;
        """
        bronze_dir = self.cfg.local_bronze_dir / self.cfg.table_name

        csv_files = self._resolve_local_csv_files()
        if not csv_files:
            logger.warning(
                "No CSV files found for table '%s' under %s – skipping. "
                "Expected partition strategy: %s",
                self.cfg.table_name,
                self.cfg.local_raw_dir,
                self._table_def.partition_strategy,
            )
            return

        bronze_dir.mkdir(parents=True, exist_ok=True)
        delta_path = str(bronze_dir.resolve())

        con = duckdb.connect()
        con.execute("INSTALL delta; LOAD delta;")

        # Idempotency: snapshot of already-processed files
        ingested_files: set[str] = self._already_ingested_files(con, delta_path)
        if ingested_files:
            logger.info(
                "Found %d previously ingested file(s) in Bronze table – these will be skipped.",
                len(ingested_files),
            )

        source_system = self.cfg.source_system
        ingested_at = self._ingested_at
        batch_id = self._batch_id
        skipped = 0
        appended = 0

        for csv_file in csv_files:
            source_file = str(csv_file.resolve())

            if source_file in ingested_files:
                logger.warning("  SKIP (already ingested): %s", source_file)
                skipped += 1
                continue

            logger.info("  Appending %s → %s", source_file, delta_path)
            arrow_table: pa.Table = con.execute(
                f"""
                SELECT
                    *,
                    '{source_system}'     AS _source_system,
                    '{source_file}'       AS _source_file,
                    '{ingested_at}'       AS _ingested_at,
                    '{batch_id}'          AS _batch_id
                FROM read_csv_auto('{source_file}', header = true)
                """
            ).fetch_arrow_table()
            write_deltalake(delta_path, arrow_table, mode="append")
            appended += 1

        con.close()
        logger.info(
            "Bronze local ingestion complete | table=%s appended=%d skipped=%d path=%s",
            self.cfg.table_name,
            appended,
            skipped,
            delta_path,
        )

    # ------------------------------------------------------------------
    # Cloud mode – PySpark Auto Loader → Databricks Delta table
    # ------------------------------------------------------------------

    def _build_s3_source_path(self) -> str:
        """
        Construct the S3 source path, scoping to a single date partition when
        ``partition_date`` is set and the table uses a daily partition strategy.

        Partition path patterns
        -----------------------
        daily (scoped)      : s3://<bucket>/<prefix>/<table>/year=YYYY/month=MM/day=DD/
        daily (full scan)   : s3://<bucket>/<prefix>/<table>/
        monthly_snapshot    : s3://<bucket>/<prefix>/<table>/
        full_snapshot       : s3://<bucket>/<prefix>/<table>/
        """
        prefix = f"{self.cfg.s3_prefix}/" if self.cfg.s3_prefix else ""
        base = f"s3://{self.cfg.s3_bucket}/{prefix}{self.cfg.table_name}"

        if (
            self.cfg.partition_date
            and self._table_def.partition_strategy == PartitionStrategy.DAILY
        ):
            dt = datetime.strptime(self.cfg.partition_date, "%Y-%m-%d")
            return (
                f"{base}/"
                f"year={dt.year}/"
                f"month={dt.month:02d}/"
                f"day={dt.day:02d}/"
            )

        return f"{base}/"

    def _run_databricks(self, spark: object) -> None:
        """
        Stream new S3 files into a managed Unity Catalog Delta table using
        Auto Loader (trigger: availableNow = exactly-once batch semantics).

        Idempotency
        -----------
        Auto Loader persists a checkpoint at ``checkpoint_base/<table_name>/``.
        The checkpoint records every committed S3 object path so re-triggering
        the job never re-delivers files regardless of how many times it runs.

        Schema tracking
        ---------------
        ``cloudFiles.schemaLocation`` is stored in a sub-path of the checkpoint
        directory, isolating schema evolution from offset tracking so that adding
        a source column does not reset the processed-file history.
        """
        from pyspark.sql import SparkSession  # type: ignore[import]
        from pyspark.sql import functions as F  # type: ignore[import]

        assert isinstance(spark, SparkSession)

        s3_source = self._build_s3_source_path()
        target_table = (
            f"{self.cfg.databricks_catalog}"
            f".{self.cfg.databricks_schema}"
            f".{self.cfg.table_name}"
        )
        # Per-table checkpoint – never share across tables.
        checkpoint_path = f"{self.cfg.checkpoint_base}/{self.cfg.table_name}"

        logger.info("Table definition     : %s (pk=%s, partition=%s)",
                    self._table_def.table_name,
                    self._table_def.primary_keys,
                    self._table_def.partition_strategy)
        logger.info("Auto Loader source   : %s", s3_source)
        logger.info("Target Delta table   : %s", target_table)
        logger.info("Auto Loader checkpoint: %s", checkpoint_path)

        source_system = self.cfg.source_system
        ingested_at = self._ingested_at
        batch_id = self._batch_id

        (
            spark.readStream.format("cloudFiles")
            .option("cloudFiles.format", "csv")
            .option("cloudFiles.inferColumnTypes", "true")
            # Schema stored separately from offset tracking so schema changes
            # do not invalidate the file-processed history.
            .option("cloudFiles.schemaLocation", f"{checkpoint_path}/_schema")
            .load(s3_source)
            .withColumn("_source_system", F.lit(source_system))
            .withColumn("_source_file", F.input_file_name())
            .withColumn("_ingested_at", F.lit(ingested_at).cast("timestamp"))
            .withColumn("_batch_id", F.lit(batch_id))
            .writeStream.format("delta")
            .outputMode("append")
            # The checkpoint records every committed file; re-runs resume from
            # the last committed micro-batch offset automatically.
            .option("checkpointLocation", checkpoint_path)
            .option("mergeSchema", "true")
            # availableNow: process all pending files then stop – exactly-once
            # batch semantics without an always-on streaming job.
            .trigger(availableNow=True)
            .toTable(target_table)
            .awaitTermination()
        )

        logger.info(
            "Databricks Bronze ingestion complete | table=%s pk=%s",
            target_table,
            self._table_def.primary_keys,
        )
