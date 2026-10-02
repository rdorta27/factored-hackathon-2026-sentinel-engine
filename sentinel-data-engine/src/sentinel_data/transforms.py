"""
Canonical SQL constants and query-builder helpers shared across all Medallion layers.

Both ``local_runner.py`` (DuckDB) and ``build_gold.py`` (DuckDB local + PySpark
Databricks) import from this module so every dataset constant and business rule
has a single authoritative definition.

Engine notes
------------
DuckDB and Databricks SQL differ in two constructs used here:

    DATEDIFF  – DuckDB: ``DATEDIFF('day', earlier, later)``
                Databricks SQL: ``DATEDIFF(later, earlier)``

    Date cast – DuckDB: ``TRY_CAST(col AS TIMESTAMP)``
                Databricks SQL: ``CAST(col AS TIMESTAMP)``

The query-builder functions accept an ``engine`` parameter ('duckdb' | 'databricks')
and emit the appropriate variant.
"""

from __future__ import annotations

from typing import Literal

# ---------------------------------------------------------------------------
# Shared dataset constants
# ---------------------------------------------------------------------------

DATASET_CUTOFF_DATE: str = "2026-06-17"
DISPUTE_ELIGIBILITY_DAYS: int = 90

Engine = Literal["duckdb", "databricks"]

# Columns that carry country values and must be normalised (REQ-0015).
COUNTRY_NORM_COLUMNS: frozenset[str] = frozenset({"country", "transaction_country"})

# ---------------------------------------------------------------------------
# Country normalisation helper
# ---------------------------------------------------------------------------


def country_norm_expr(col: str) -> str:
    """Return a SQL CASE expression that canonicalises Mexico → México for *col*."""
    return f"CASE WHEN TRIM({col}) = 'Mexico' THEN 'México' ELSE COALESCE(TRIM({col}), 'UNSPECIFIED') END"


# ---------------------------------------------------------------------------
# Silver canonical SELECT clauses
# (source table is parameterised so the same SQL works for both bronze_<table>
# views in local_runner and delta_scan paths in transform_silver)
# ---------------------------------------------------------------------------


def silver_customers_sql(source: str) -> str:
    return f"""
        SELECT DISTINCT
            customer_id,
            COALESCE(first_name,       'UNSPECIFIED') AS first_name,
            COALESCE(last_name,        'UNSPECIFIED') AS last_name,
            COALESCE(document_type,    'UNSPECIFIED') AS document_type,
            document_number,
            date_of_birth,
            gender,
            COALESCE(city,             'UNSPECIFIED') AS city,
            COALESCE(state,            'UNSPECIFIED') AS state,
            {country_norm_expr('country')}             AS country,
            COALESCE(segment,          'UNSPECIFIED') AS segment,
            COALESCE(customer_status,  'UNSPECIFIED') AS customer_status,
            COALESCE(detected_accent,  'UNSPECIFIED') AS detected_accent,
            registration_date,
            registration_branch_id,
            last_updated,
            accepts_marketing,
            credit_score,
            TRY_CAST(estimated_monthly_income AS DOUBLE) AS estimated_monthly_income
        FROM {source}
    """


def silver_transactions_sql(source: str) -> str:
    return f"""
        SELECT DISTINCT
            transaction_id,
            transaction_date,
            process_date,
            product_id,
            customer_id,
            COALESCE(transaction_type,     'UNSPECIFIED') AS transaction_type,
            COALESCE(transaction_category, 'UNSPECIFIED') AS transaction_category,
            CAST(amount AS DOUBLE)                        AS amount,
            COALESCE(currency,             'UNSPECIFIED') AS currency,
            TRY_CAST(amount_usd AS DOUBLE)                AS amount_usd,
            COALESCE(channel,              'UNSPECIFIED') AS channel,
            branch_id,
            {country_norm_expr('transaction_country')}    AS transaction_country,
            COALESCE(transaction_status,   'UNSPECIFIED') AS transaction_status,
            is_fraud,
            TRY_CAST(fraud_score AS DOUBLE)               AS fraud_score,
            COALESCE(merchant_name,        'UNSPECIFIED') AS merchant_name,
            COALESCE(merchant_category,    'UNSPECIFIED') AS merchant_category
        FROM {source}
    """


def silver_products_sql(source: str) -> str:
    return f"""
        SELECT DISTINCT
            product_id,
            customer_id,
            COALESCE(product_type,    'UNSPECIFIED') AS product_type,
            product_number,
            COALESCE(product_status,  'UNSPECIFIED') AS product_status,
            COALESCE(currency,        'UNSPECIFIED') AS currency,
            TRY_CAST(current_balance  AS DOUBLE)     AS current_balance,
            TRY_CAST(credit_limit     AS DOUBLE)     AS credit_limit,
            TRY_CAST(interest_rate    AS DOUBLE)     AS interest_rate,
            opening_date,
            expiration_date,
            opening_branch_id,
            COALESCE(opening_channel, 'UNSPECIFIED') AS opening_channel,
            has_linked_app,
            days_past_due,
            last_updated
        FROM {source}
    """


def silver_complaints_sql(source: str) -> str:
    """
    Canonical Silver complaints SELECT.

    Raw schema column mapping vs. earlier (incorrect) assumptions:
      affected_product_id  → product_id
      claimed_amount       → claimed_amount   (not compensation_amount)
      compensation_granted → compensation_granted
      resolution           → resolution_notes (renamed for downstream clarity)
      origin_interaction_id kept for CCI join lineage
    """
    return f"""
        SELECT DISTINCT
            complaint_id,
            process_date,
            customer_id,
            affected_product_id                           AS product_id,
            assigned_agent_id,
            origin_interaction_id,
            TRY_CAST(creation_date   AS DATE)            AS creation_date,
            TRY_CAST(resolution_date AS DATE)            AS resolution_date,
            TRY_CAST(closing_date    AS DATE)            AS closing_date,
            COALESCE(case_type,           'UNSPECIFIED') AS case_type,
            COALESCE(category,            'UNSPECIFIED') AS category,
            COALESCE(subcategory,         'UNSPECIFIED') AS subcategory,
            COALESCE(reception_channel,   'UNSPECIFIED') AS reception_channel,
            COALESCE(description,         'UNSPECIFIED') AS description,
            COALESCE(priority,            'UNSPECIFIED') AS priority,
            COALESCE(status,              'UNSPECIFIED') AS status,
            sla_breached,
            COALESCE(resolution,          'UNSPECIFIED') AS resolution_notes,
            TRY_CAST(claimed_amount       AS DOUBLE)     AS claimed_amount,
            COALESCE(currency,            'UNSPECIFIED') AS currency,
            compensation_granted,
            is_repeat_complainer
        FROM {source}
    """


def silver_service_agents_sql(source: str) -> str:
    return f"""
        SELECT DISTINCT
            agent_id,
            COALESCE(first_name,         'UNSPECIFIED') AS first_name,
            COALESCE(last_name,          'UNSPECIFIED') AS last_name,
            COALESCE(agent_type,         'UNSPECIFIED') AS agent_type,
            COALESCE(experience_level,   'UNSPECIFIED') AS experience_level,
            COALESCE(languages,          'UNSPECIFIED') AS languages,
            COALESCE(native_accent,      'UNSPECIFIED') AS native_accent,
            COALESCE(country_of_origin,  'UNSPECIFIED') AS country_of_origin,
            COALESCE(agent_status,       'UNSPECIFIED') AS agent_status,
            COALESCE(work_shift,         'UNSPECIFIED') AS work_shift,
            hire_date,
            TRY_CAST(avg_csat AS DOUBLE)               AS avg_csat
        FROM {source}
    """


def silver_call_center_interactions_sql(source: str) -> str:
    """
    Canonical Silver call_center_interactions SELECT.

    The raw schema has NO complaint_id column.  The link to complaints is via
    silver_complaints.origin_interaction_id → interaction_id (reverse join).
    """
    return f"""
        SELECT DISTINCT
            interaction_id,
            process_date,
            customer_id,
            agent_id,
            TRY_CAST(interaction_date  AS DATE)          AS interaction_date,
            COALESCE(interaction_type, 'UNSPECIFIED')    AS interaction_type,
            COALESCE(channel,          'UNSPECIFIED')    AS channel,
            COALESCE(contact_reason,   'UNSPECIFIED')    AS contact_reason,
            COALESCE(reason_category,  'UNSPECIFIED')    AS reason_category,
            duration_seconds,
            wait_time_seconds,
            TRY_CAST(sentiment_score   AS DOUBLE)        AS sentiment_score,
            was_escalated,
            was_resolved,
            requires_followup,
            has_transcript,
            has_recording,
            COALESCE(detected_sentiment, 'UNSPECIFIED')  AS detected_sentiment
        FROM {source}
    """


def silver_satisfaction_surveys_sql(source: str) -> str:
    """
    Canonical Silver satisfaction_surveys SELECT.

    Raw schema uses interaction_id (not complaint_id) as the FK to
    call_center_interactions.
    """
    return f"""
        SELECT DISTINCT
            survey_id,
            process_date,
            customer_id,
            interaction_id,
            agent_id,
            TRY_CAST(survey_date AS DATE)              AS survey_date,
            COALESCE(survey_type,   'UNSPECIFIED')     AS survey_type,
            COALESCE(send_channel,  'UNSPECIFIED')     AS send_channel,
            TRY_CAST(main_score  AS DOUBLE)            AS main_score,
            COALESCE(open_comments, 'UNSPECIFIED')     AS comments,
            COALESCE(nps_category,  'UNSPECIFIED')     AS nps_category
        FROM {source}
    """


# ---------------------------------------------------------------------------
# Gold query builders
# ---------------------------------------------------------------------------
#
# Each function returns a complete SQL SELECT statement.  The caller wraps it
# in a CREATE TABLE / CREATE VIEW / spark.sql() as needed.
#
# silver_prefix  – table name prefix for Silver sources:
#   DuckDB local_runner : "silver_"  (views named silver_customers, etc.)
#   Databricks          : f"{cat}.{s_silver}."
#
# engine         – controls engine-specific SQL dialect differences.
# ---------------------------------------------------------------------------


def gold_customer_360_sql(
    silver_prefix: str = "silver_",
    engine: Engine = "duckdb",
) -> str:
    return f"""
        WITH product_agg AS (
            SELECT
                customer_id,
                COUNT(*)                                            AS total_products,
                COUNT(*) FILTER (WHERE product_status = 'ACTIVE')  AS active_products,
                SUM(current_balance)                               AS total_balance,
                MAX(product_type)                                  AS primary_product_type
            FROM {silver_prefix}products
            GROUP BY customer_id
        ),
        complaint_agg AS (
            SELECT
                customer_id,
                COUNT(*)                                           AS total_complaints,
                COUNT(*) FILTER (
                    WHERE status NOT IN ('CLOSED', 'RESOLVED')
                )                                                  AS active_disputes,
                BOOL_OR(is_repeat_complainer)                     AS is_repeat_complainer,
                SUM(COALESCE(claimed_amount, 0))                  AS total_claimed_amount
            FROM {silver_prefix}complaints
            GROUP BY customer_id
        ),
        survey_agg AS (
            SELECT
                customer_id,
                AVG(main_score) AS avg_csat_score,
                COUNT(*)        AS total_surveys
            FROM {silver_prefix}satisfaction_surveys
            GROUP BY customer_id
        )
        SELECT
            c.customer_id,
            c.first_name, c.last_name, c.document_type, c.document_number,
            c.date_of_birth, c.city, c.state, c.country, c.segment,
            c.customer_status, c.registration_date, c.credit_score,
            COALESCE(pa.total_products,         0)     AS total_products,
            COALESCE(pa.active_products,        0)     AS active_products,
            COALESCE(pa.total_balance,          0.0)   AS total_balance,
            pa.primary_product_type,
            COALESCE(ca.total_complaints,       0)     AS total_complaints,
            COALESCE(ca.active_disputes,        0)     AS active_disputes,
            COALESCE(ca.is_repeat_complainer,   FALSE) AS is_repeat_complainer,
            COALESCE(ca.total_claimed_amount,   0.0)   AS total_claimed_amount,
            sa.avg_csat_score,
            COALESCE(sa.total_surveys,          0)     AS total_surveys,
            CASE
                WHEN COALESCE(ca.active_disputes, 0) >= 3
                     OR COALESCE(ca.is_repeat_complainer, FALSE)
                    THEN 'HIGH'
                WHEN COALESCE(ca.active_disputes, 0) BETWEEN 1 AND 2
                    THEN 'MEDIUM'
                ELSE 'LOW'
            END AS dispute_risk_level,
            DATE '{DATASET_CUTOFF_DATE}' AS snapshot_date
        FROM {silver_prefix}customers c
        LEFT JOIN product_agg  pa ON pa.customer_id = c.customer_id
        LEFT JOIN complaint_agg ca ON ca.customer_id = c.customer_id
        LEFT JOIN survey_agg   sa ON sa.customer_id  = c.customer_id
    """


def _datediff_days(earlier: str, later: str, engine: Engine) -> str:
    """Return a DATEDIFF expression that computes (later - earlier) in days."""
    if engine == "duckdb":
        return f"DATEDIFF('day', {earlier}, {later})"
    # Databricks SQL / PySpark SQL: DATEDIFF(end, start)
    return f"DATEDIFF({later}, {earlier})"


def _cast_to_timestamp(col: str, engine: Engine) -> str:
    cast_fn = "TRY_CAST" if engine == "duckdb" else "CAST"
    return f"{cast_fn}({col} AS TIMESTAMP)"


def gold_eligible_transactions_sql(
    silver_prefix: str = "silver_",
    engine: Engine = "duckdb",
) -> str:
    """
    Build gold_dispute_eligible_transactions.

    is_disputed is derived from complaints that have an open status and share
    both customer_id and product_id with the transaction.  This is the closest
    available proxy since the raw complaints schema has no referenced_transaction_id.

    days_since_transaction uses the fixed dataset cutoff date (DATASET_CUTOFF_DATE)
    — never CURRENT_DATE — so eligibility is reproducible regardless of run time.
    """
    ts_cast = _cast_to_timestamp("t.transaction_date", engine)
    cutoff_ts = _cast_to_timestamp(f"'{DATASET_CUTOFF_DATE}'", engine)
    days_expr = _datediff_days(ts_cast, cutoff_ts, engine)
    return f"""
        WITH open_complaints AS (
            SELECT DISTINCT customer_id, product_id
            FROM {silver_prefix}complaints
            WHERE status NOT IN ('CLOSED', 'RESOLVED')
        )
        SELECT
            t.transaction_id,
            t.transaction_date,
            t.process_date,
            t.product_id,
            t.customer_id,
            t.transaction_type,
            t.amount,
            t.currency,
            t.channel,
            t.transaction_country,
            t.transaction_status,
            t.is_fraud,
            t.fraud_score,
            t.merchant_name,
            t.merchant_category,
            c.first_name   AS customer_first_name,
            c.last_name    AS customer_last_name,
            c.segment      AS customer_segment,
            c.country      AS customer_country,
            c.credit_score AS customer_credit_score,
            (oc.customer_id IS NOT NULL)                      AS is_disputed,
            {days_expr}                                       AS days_since_transaction,
            (
                oc.customer_id IS NULL
                AND {days_expr} <= {DISPUTE_ELIGIBILITY_DAYS}
                AND t.transaction_status NOT IN ('Reversed', 'Refunded')
            )                                                 AS is_eligible_for_dispute,
            DATE '{DATASET_CUTOFF_DATE}'                      AS snapshot_date
        FROM {silver_prefix}transactions t
        LEFT JOIN {silver_prefix}customers c  ON c.customer_id = t.customer_id
        LEFT JOIN open_complaints         oc  ON oc.customer_id = t.customer_id
                                             AND oc.product_id  = t.product_id
    """


def gold_service_eligible_transactions_sql(source: str) -> str:
    """PII-free projection of gold_dispute_eligible_transactions (ADR 008)."""
    return f"""
        SELECT
            transaction_id,
            transaction_date,
            process_date,
            product_id,
            customer_id,
            transaction_type,
            amount,
            currency,
            channel,
            transaction_country,
            transaction_status,
            is_fraud,
            fraud_score,
            merchant_name,
            merchant_category,
            customer_segment,
            customer_country,
            is_disputed,
            days_since_transaction,
            is_eligible_for_dispute,
            snapshot_date
        FROM {source}
    """


def gold_cases_summary_sql(
    silver_prefix: str = "silver_",
    engine: Engine = "duckdb",
) -> str:
    """
    Build gold_dispute_cases_summary.

    Joins complaints → customers → products → service_agents →
    call_center_interactions (via silver_complaints.origin_interaction_id →
    silver_call_center_interactions.interaction_id).

    No complaint_id column exists in raw call_center_interactions; the reverse
    join through origin_interaction_id is the correct linkage.
    """
    cutoff_date = f"DATE '{DATASET_CUTOFF_DATE}'"
    if engine == "duckdb":
        age_expr = (
            f"DATE_DIFF('day', comp.creation_date::DATE, "
            f"COALESCE(comp.resolution_date::DATE, {cutoff_date}))"
        )
    else:
        # Databricks SQL: DATEDIFF(end, start)
        age_expr = (
            f"DATEDIFF(COALESCE(comp.resolution_date, {cutoff_date}), comp.creation_date)"
        )
    return f"""
        SELECT
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
            comp.claimed_amount,
            comp.compensation_granted,
            comp.is_repeat_complainer,
            comp.customer_id,
            c.first_name   AS customer_first_name,
            c.last_name    AS customer_last_name,
            c.segment      AS customer_segment,
            c.country      AS customer_country,
            c.credit_score AS customer_credit_score,
            comp.product_id,
            p.product_type,
            p.product_number,
            p.currency       AS product_currency,
            p.current_balance AS product_balance,
            comp.assigned_agent_id,
            sa.first_name        AS agent_first_name,
            sa.last_name         AS agent_last_name,
            sa.agent_type,
            sa.experience_level  AS agent_experience_level,
            sa.languages         AS agent_languages,
            oi.interaction_id    AS origin_interaction_id,
            oi.interaction_date  AS origin_interaction_date,
            oi.channel           AS origin_channel,
            oi.contact_reason    AS origin_contact_reason,
            oi.sentiment_score   AS origin_sentiment_score,
            oi.was_escalated     AS origin_was_escalated,
            {age_expr}           AS case_age_days,
            {cutoff_date}        AS snapshot_date
        FROM {silver_prefix}complaints comp
        LEFT JOIN {silver_prefix}customers          c  ON c.customer_id    = comp.customer_id
        LEFT JOIN {silver_prefix}products           p  ON p.product_id     = comp.product_id
        LEFT JOIN {silver_prefix}service_agents     sa ON sa.agent_id      = comp.assigned_agent_id
        LEFT JOIN {silver_prefix}call_center_interactions oi
                                                       ON oi.interaction_id = comp.origin_interaction_id
    """
