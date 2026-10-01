"""
Unified CLI entry point for Databricks python_wheel_task execution.

Routes to the Bronze ingestor, Silver transformer, Gold builder, or the full
local DuckDB pipeline runner based on --layer.

Local examples
--------------
    python -m sentinel_data --layer bronze --table-name transactions
    python -m sentinel_data --layer silver --table-name transactions
    python -m sentinel_data --layer gold
    python -m sentinel_data --layer all --duckdb-out data/gold_bank.duckdb

Databricks Job task example (python_wheel_task)
------------------------------------------------
    entry_point: sentinel_data.__main__
    parameters:
      - "--layer=bronze"
      - "--table-name=transactions"
      - "--run-mode=databricks"
      - "--s3-bucket=${S3_BUCKET}"
"""

from __future__ import annotations

import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sentinel Data Engine – Medallion Pipeline CLI")

    p.add_argument(
        "--layer",
        required=True,
        choices=["bronze", "silver", "gold", "all"],
        help=(
            "Pipeline layer to execute. Use 'all' to run the full Bronze→Silver→Gold "
            "workflow locally against a persistent DuckDB file."
        ),
    )
    # Gold builds all tables at once so --table-name is not needed; default to 'all'.
    p.add_argument("--table-name", default="all")
    p.add_argument("--run-mode", default="local", choices=["local", "databricks"])

    # 'all' layer local runner
    p.add_argument(
        "--duckdb-out",
        default="data/gold_bank.duckdb",
        help="Persistent DuckDB file path used by --layer=all (local runner).",
    )
    p.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Root directory holding raw CSV table sub-folders (used by --layer=all).",
    )
    p.add_argument(
        "--report-out",
        default="data_quality_report.md",
        help="Output path for the Markdown data-quality report (used by --layer=all).",
    )

    # Bronze-specific
    p.add_argument("--s3-bucket", default="")
    p.add_argument("--s3-prefix", default="")
    p.add_argument("--source-system", default="s3")

    # Databricks / Unity Catalog (shared)
    p.add_argument("--databricks-catalog", default="sentinel")
    p.add_argument("--databricks-schema", default="bronze")   # Bronze target schema

    # Silver-specific
    p.add_argument("--databricks-schema-bronze", default="bronze")
    p.add_argument("--databricks-schema-silver", default="silver")

    return p.parse_args()


def main() -> None:
    args = _parse_args()

    if args.layer == "bronze":
        from sentinel_data.bronze.ingest_bronze import BronzeIngestorConfig, BronzeIngestor, RunMode

        cfg = BronzeIngestorConfig(
            table_name=args.table_name,
            run_mode=RunMode(args.run_mode),
            source_system=args.source_system,
            s3_bucket=args.s3_bucket,
            s3_prefix=args.s3_prefix,
            databricks_catalog=args.databricks_catalog,
            databricks_schema=args.databricks_schema,
        )
        ingestor = BronzeIngestor(cfg)
        if args.run_mode == "databricks":
            from pyspark.sql import SparkSession  # type: ignore[import]
            spark = SparkSession.builder.getOrCreate()
            ingestor.run(spark=spark)
        else:
            ingestor.run()

    elif args.layer == "gold":
        from sentinel_data.gold.build_gold import GoldBuilderConfig, GoldBuilder, RunMode as GoldRunMode

        cfg_g = GoldBuilderConfig(
            run_mode=GoldRunMode(args.run_mode),
            databricks_catalog=args.databricks_catalog,
            databricks_schema_silver=args.databricks_schema_silver,  # was incorrectly schema_bronze
            databricks_schema_gold="gold",
        )
        builder = GoldBuilder(cfg_g)
        if args.run_mode == "databricks":
            from pyspark.sql import SparkSession  # type: ignore[import]
            spark = SparkSession.builder.getOrCreate()
            builder.run(spark=spark)
        else:
            builder.run()

    elif args.layer == "all":
        from sentinel_data.local_runner import LocalPipelineRunner

        LocalPipelineRunner(
            raw_dir=args.raw_dir,
            duckdb_path=args.duckdb_out,
            report_path=args.report_out,
        ).run()

    elif args.layer == "silver":
        from sentinel_data.silver.transform_silver import (
            SilverTransformerConfig,
            SilverTransformer,
            RunMode,
        )

        cfg_s = SilverTransformerConfig(
            table_name=args.table_name,
            run_mode=RunMode(args.run_mode),
            databricks_catalog=args.databricks_catalog,
            databricks_schema_bronze=args.databricks_schema_bronze,
            databricks_schema_silver=args.databricks_schema_silver,
        )
        transformer = SilverTransformer(cfg_s)
        if args.run_mode == "databricks":
            from pyspark.sql import SparkSession  # type: ignore[import]
            spark = SparkSession.builder.getOrCreate()
            transformer.run(spark=spark)
        else:
            transformer.run()


if __name__ == "__main__":
    main()
