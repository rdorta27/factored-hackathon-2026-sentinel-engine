"""
Unified CLI entry point for Databricks python_wheel_task execution.

Routes to the Bronze ingestor or Silver transformer based on --layer.

Local examples
--------------
    python -m sentinel_data --layer bronze --table-name transactions
    python -m sentinel_data --layer silver --table-name transactions

Databricks Job task example (python_wheel_task)
------------------------------------------------
    entry_point: sentinel_data.__main__
    parameters:
      - "--layer=bronze"
      - "--table-name=transactions"
      - "--run-mode=databricks"
      - "--s3-bucket=factored-datathon-2026-s3-157725502942-us-east-2-an"
"""

from __future__ import annotations

import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sentinel Data Engine – Medallion Pipeline CLI")

    p.add_argument("--layer", required=True, choices=["bronze", "silver"])
    p.add_argument("--table-name", required=True)
    p.add_argument("--run-mode", default="local", choices=["local", "databricks"])

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
