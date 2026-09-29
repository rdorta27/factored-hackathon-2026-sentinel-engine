"""
LATAM Bank dataset catalog – single source of truth for all 13 source tables.

Each ``TableDefinition`` captures:
  - Primary key columns (single or composite)
  - Partition column and strategy (daily / monthly_snapshot / full_snapshot)
  - Silver quality rules derived from NOT NULL + PK constraints in the schema

Usage
-----
    from sentinel_data.catalog import TABLE_REGISTRY, get_table

    defn = get_table("transactions")
    defn.primary_keys        # ["transaction_id"]
    defn.partition_column    # "process_date"
    defn.quality_rules       # list[QualityRule]
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------


class PartitionStrategy(str, Enum):
    """How the source table is partitioned on S3."""

    DAILY = "daily"                   # year/month/day  (fact tables)
    MONTHLY_SNAPSHOT = "monthly_snapshot"  # year/month      (slowly-changing dims)
    FULL_SNAPSHOT = "full_snapshot"   # single flat prefix (reference/static dims)


class QualityRule(BaseModel):
    """A single named data-quality predicate for the Silver validation step."""

    rule_name: str = Field(..., description="Unique identifier for this rule")
    column: str = Field(..., description="Column the predicate targets")
    sql_predicate: str = Field(
        ...,
        description=(
            "SQL boolean expression returning TRUE for a VALID row. "
            "May reference any column in the table."
        ),
    )


class TableDefinition(BaseModel):
    """Schema metadata and quality contract for one source table."""

    table_name: str = Field(..., description="Matches the S3 prefix and local directory name")
    primary_keys: list[str] = Field(..., description="Business key columns (order matters for MERGE)")
    partition_column: str = Field(..., description="Column used for S3 date-partitioning")
    partition_strategy: PartitionStrategy = Field(...)
    approximate_rows: int = Field(..., description="Expected row count – used for cluster sizing hints")
    quality_rules: list[QualityRule] = Field(
        default_factory=list,
        description="Silver validation rules derived from NOT NULL / domain constraints",
    )

    @property
    def merge_condition(self) -> str:
        """Return a SQL JOIN predicate for Delta MERGE on all primary key columns."""
        return " AND ".join(f"target.{k} = source.{k}" for k in self.primary_keys)

    @property
    def dedup_partition_keys(self) -> str:
        """Comma-separated primary key list for ROW_NUMBER PARTITION BY."""
        return ", ".join(self.primary_keys)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _rules(*pairs: tuple[str, str, str]) -> list[QualityRule]:
    """
    Shorthand builder: each tuple is (rule_name, column, sql_predicate).
    Keeps the registry block below concise.
    """
    return [QualityRule(rule_name=n, column=c, sql_predicate=p) for n, c, p in pairs]


# ---------------------------------------------------------------------------
# Table registry – 13 tables from the LATAM Bank dataset
# ---------------------------------------------------------------------------
#
# Quality rules encode the NOT NULL constraints and domain invariants declared
# in the data dictionary.  Additional semantic rules (e.g. amount > 0) can be
# appended per table without touching the transformer logic.
# ---------------------------------------------------------------------------

TABLE_REGISTRY: Final[dict[str, TableDefinition]] = {

    # ── Dimension tables ────────────────────────────────────────────────────

    "customers": TableDefinition(
        table_name="customers",
        primary_keys=["customer_id"],
        partition_column="last_updated",
        partition_strategy=PartitionStrategy.MONTHLY_SNAPSHOT,
        approximate_rows=150_000,
        quality_rules=_rules(
            ("customer_id_not_null",        "customer_id",        "customer_id IS NOT NULL"),
            ("document_number_not_null",    "document_number",    "document_number IS NOT NULL"),
            ("document_type_not_null",      "document_type",      "document_type IS NOT NULL"),
            ("first_name_not_null",         "first_name",         "first_name IS NOT NULL AND LENGTH(TRIM(first_name)) > 0"),
            ("last_name_not_null",          "last_name",          "last_name IS NOT NULL AND LENGTH(TRIM(last_name)) > 0"),
            ("date_of_birth_not_null",      "date_of_birth",      "date_of_birth IS NOT NULL"),
            ("city_not_null",               "city",               "city IS NOT NULL AND LENGTH(TRIM(city)) > 0"),
            ("state_not_null",              "state",              "state IS NOT NULL AND LENGTH(TRIM(state)) > 0"),
            ("country_not_null",            "country",            "country IS NOT NULL AND LENGTH(TRIM(country)) > 0"),
            ("segment_not_null",            "segment",            "segment IS NOT NULL AND LENGTH(TRIM(segment)) > 0"),
            ("registration_date_not_null",  "registration_date",  "registration_date IS NOT NULL"),
            ("registration_branch_not_null","registration_branch_id", "registration_branch_id IS NOT NULL"),
            ("customer_status_not_null",    "customer_status",    "customer_status IS NOT NULL AND LENGTH(TRIM(customer_status)) > 0"),
            ("last_updated_not_null",       "last_updated",       "last_updated IS NOT NULL"),
            ("accepts_marketing_not_null",  "accepts_marketing",  "accepts_marketing IS NOT NULL"),
        ),
    ),

    "products": TableDefinition(
        table_name="products",
        primary_keys=["product_id"],
        partition_column="last_updated",
        partition_strategy=PartitionStrategy.MONTHLY_SNAPSHOT,
        approximate_rows=400_000,
        quality_rules=_rules(
            ("product_id_not_null",       "product_id",       "product_id IS NOT NULL"),
            ("customer_id_not_null",      "customer_id",      "customer_id IS NOT NULL"),
            ("product_type_not_null",     "product_type",     "product_type IS NOT NULL AND LENGTH(TRIM(product_type)) > 0"),
            ("product_number_not_null",   "product_number",   "product_number IS NOT NULL AND LENGTH(TRIM(product_number)) > 0"),
            ("currency_not_null",         "currency",         "currency IS NOT NULL AND LENGTH(currency) = 3"),
            ("current_balance_not_null",  "current_balance",  "current_balance IS NOT NULL"),
            ("opening_date_not_null",     "opening_date",     "opening_date IS NOT NULL"),
            ("opening_branch_not_null",   "opening_branch_id","opening_branch_id IS NOT NULL"),
            ("product_status_not_null",   "product_status",   "product_status IS NOT NULL AND LENGTH(TRIM(product_status)) > 0"),
            ("opening_channel_not_null",  "opening_channel",  "opening_channel IS NOT NULL AND LENGTH(TRIM(opening_channel)) > 0"),
            ("has_linked_app_not_null",   "has_linked_app",   "has_linked_app IS NOT NULL"),
            ("last_updated_not_null",     "last_updated",     "last_updated IS NOT NULL"),
        ),
    ),

    "branches": TableDefinition(
        table_name="branches",
        primary_keys=["branch_id"],
        partition_column="branch_opening_date",
        partition_strategy=PartitionStrategy.FULL_SNAPSHOT,
        approximate_rows=350,
        quality_rules=_rules(
            ("branch_id_not_null",          "branch_id",          "branch_id IS NOT NULL"),
            ("branch_code_not_null",        "branch_code",        "branch_code IS NOT NULL AND LENGTH(TRIM(branch_code)) > 0"),
            ("branch_name_not_null",        "branch_name",        "branch_name IS NOT NULL AND LENGTH(TRIM(branch_name)) > 0"),
            ("branch_type_not_null",        "branch_type",        "branch_type IS NOT NULL AND LENGTH(TRIM(branch_type)) > 0"),
            ("address_not_null",            "address",            "address IS NOT NULL AND LENGTH(TRIM(address)) > 0"),
            ("city_not_null",               "city",               "city IS NOT NULL AND LENGTH(TRIM(city)) > 0"),
            ("state_not_null",              "state",              "state IS NOT NULL AND LENGTH(TRIM(state)) > 0"),
            ("country_not_null",            "country",            "country IS NOT NULL AND LENGTH(TRIM(country)) > 0"),
            ("geographic_zone_not_null",    "geographic_zone",    "geographic_zone IS NOT NULL AND LENGTH(TRIM(geographic_zone)) > 0"),
            ("phone_not_null",              "phone",              "phone IS NOT NULL AND LENGTH(TRIM(phone)) > 0"),
            ("opening_time_not_null",       "opening_time",       "opening_time IS NOT NULL"),
            ("closing_time_not_null",       "closing_time",       "closing_time IS NOT NULL"),
            ("has_atms_not_null",           "has_atms",           "has_atms IS NOT NULL"),
            ("has_teller_windows_not_null", "has_teller_windows", "has_teller_windows IS NOT NULL"),
            ("branch_opening_date_not_null","branch_opening_date","branch_opening_date IS NOT NULL"),
            ("branch_status_not_null",      "branch_status",      "branch_status IS NOT NULL AND LENGTH(TRIM(branch_status)) > 0"),
        ),
    ),

    "service_agents": TableDefinition(
        table_name="service_agents",
        primary_keys=["agent_id"],
        partition_column="hire_date",
        partition_strategy=PartitionStrategy.MONTHLY_SNAPSHOT,
        approximate_rows=1_200,
        quality_rules=_rules(
            ("agent_id_not_null",           "agent_id",           "agent_id IS NOT NULL"),
            ("employee_code_not_null",      "employee_code",      "employee_code IS NOT NULL AND LENGTH(TRIM(employee_code)) > 0"),
            ("first_name_not_null",         "first_name",         "first_name IS NOT NULL AND LENGTH(TRIM(first_name)) > 0"),
            ("last_name_not_null",          "last_name",          "last_name IS NOT NULL AND LENGTH(TRIM(last_name)) > 0"),
            ("email_not_null",              "email",              "email IS NOT NULL AND LENGTH(TRIM(email)) > 0"),
            ("native_accent_not_null",      "native_accent",      "native_accent IS NOT NULL AND LENGTH(TRIM(native_accent)) > 0"),
            ("country_of_origin_not_null",  "country_of_origin",  "country_of_origin IS NOT NULL AND LENGTH(TRIM(country_of_origin)) > 0"),
            ("agent_type_not_null",         "agent_type",         "agent_type IS NOT NULL AND LENGTH(TRIM(agent_type)) > 0"),
            ("experience_level_not_null",   "experience_level",   "experience_level IS NOT NULL AND LENGTH(TRIM(experience_level)) > 0"),
            ("languages_not_null",          "languages",          "languages IS NOT NULL AND LENGTH(TRIM(languages)) > 0"),
            ("hire_date_not_null",          "hire_date",          "hire_date IS NOT NULL"),
            ("agent_status_not_null",       "agent_status",       "agent_status IS NOT NULL AND LENGTH(TRIM(agent_status)) > 0"),
            ("work_shift_not_null",         "work_shift",         "work_shift IS NOT NULL AND LENGTH(TRIM(work_shift)) > 0"),
        ),
    ),

    "marketing_campaigns": TableDefinition(
        table_name="marketing_campaigns",
        primary_keys=["campaign_id"],
        partition_column="start_date",
        partition_strategy=PartitionStrategy.FULL_SNAPSHOT,
        approximate_rows=200,
        quality_rules=_rules(
            ("campaign_id_not_null",        "campaign_id",        "campaign_id IS NOT NULL"),
            ("campaign_name_not_null",      "campaign_name",      "campaign_name IS NOT NULL AND LENGTH(TRIM(campaign_name)) > 0"),
            ("campaign_type_not_null",      "campaign_type",      "campaign_type IS NOT NULL AND LENGTH(TRIM(campaign_type)) > 0"),
            ("campaign_objective_not_null", "campaign_objective", "campaign_objective IS NOT NULL AND LENGTH(TRIM(campaign_objective)) > 0"),
            ("start_date_not_null",         "start_date",         "start_date IS NOT NULL"),
            ("end_date_not_null",           "end_date",           "end_date IS NOT NULL"),
            ("campaign_status_not_null",    "campaign_status",    "campaign_status IS NOT NULL AND LENGTH(TRIM(campaign_status)) > 0"),
            ("date_range_valid",            "end_date",           "end_date >= start_date"),
        ),
    ),

    # ── Fact tables ─────────────────────────────────────────────────────────

    "transactions": TableDefinition(
        table_name="transactions",
        primary_keys=["transaction_id"],
        partition_column="process_date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=5_000_000,
        quality_rules=_rules(
            ("transaction_id_not_null",   "transaction_id",   "transaction_id IS NOT NULL"),
            ("transaction_date_not_null", "transaction_date", "transaction_date IS NOT NULL"),
            ("process_date_not_null",     "process_date",     "process_date IS NOT NULL"),
            ("product_id_not_null",       "product_id",       "product_id IS NOT NULL"),
            ("customer_id_not_null",      "customer_id",      "customer_id IS NOT NULL"),
            ("transaction_type_not_null", "transaction_type", "transaction_type IS NOT NULL AND LENGTH(TRIM(transaction_type)) > 0"),
            ("amount_not_null",           "amount",           "amount IS NOT NULL"),
            ("currency_not_null",         "currency",         "currency IS NOT NULL AND LENGTH(currency) = 3"),
            ("channel_not_null",          "channel",          "channel IS NOT NULL AND LENGTH(TRIM(channel)) > 0"),
            ("transaction_country_not_null","transaction_country","transaction_country IS NOT NULL AND LENGTH(TRIM(transaction_country)) > 0"),
            ("transaction_status_not_null","transaction_status","transaction_status IS NOT NULL AND LENGTH(TRIM(transaction_status)) > 0"),
            ("is_fraud_not_null",         "is_fraud",         "is_fraud IS NOT NULL"),
            ("fraud_score_range",         "fraud_score",      "fraud_score IS NULL OR (fraud_score >= 0.0 AND fraud_score <= 1.0)"),
        ),
    ),

    "call_center_interactions": TableDefinition(
        table_name="call_center_interactions",
        primary_keys=["interaction_id"],
        partition_column="process_date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=800_000,
        quality_rules=_rules(
            ("interaction_id_not_null",     "interaction_id",     "interaction_id IS NOT NULL"),
            ("interaction_date_not_null",   "interaction_date",   "interaction_date IS NOT NULL"),
            ("process_date_not_null",       "process_date",       "process_date IS NOT NULL"),
            ("customer_id_not_null",        "customer_id",        "customer_id IS NOT NULL"),
            ("interaction_type_not_null",   "interaction_type",   "interaction_type IS NOT NULL AND LENGTH(TRIM(interaction_type)) > 0"),
            ("channel_not_null",            "channel",            "channel IS NOT NULL AND LENGTH(TRIM(channel)) > 0"),
            ("contact_reason_not_null",     "contact_reason",     "contact_reason IS NOT NULL AND LENGTH(TRIM(contact_reason)) > 0"),
            ("reason_category_not_null",    "reason_category",    "reason_category IS NOT NULL AND LENGTH(TRIM(reason_category)) > 0"),
            ("requires_followup_not_null",  "requires_followup",  "requires_followup IS NOT NULL"),
            ("was_escalated_not_null",      "was_escalated",      "was_escalated IS NOT NULL"),
            ("has_transcript_not_null",     "has_transcript",     "has_transcript IS NOT NULL"),
            ("has_recording_not_null",      "has_recording",      "has_recording IS NOT NULL"),
            ("sentiment_score_range",       "sentiment_score",    "sentiment_score IS NULL OR (sentiment_score >= -1.0 AND sentiment_score <= 1.0)"),
        ),
    ),

    "call_transcripts": TableDefinition(
        table_name="call_transcripts",
        primary_keys=["transcript_id"],
        partition_column="process_date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=200_000,
        quality_rules=_rules(
            ("transcript_id_not_null",      "transcript_id",      "transcript_id IS NOT NULL"),
            ("interaction_id_not_null",     "interaction_id",     "interaction_id IS NOT NULL"),
            ("process_date_not_null",       "process_date",       "process_date IS NOT NULL"),
            ("customer_id_not_null",        "customer_id",        "customer_id IS NOT NULL"),
            ("agent_id_not_null",           "agent_id",           "agent_id IS NOT NULL"),
            ("full_text_not_null",          "full_text",          "full_text IS NOT NULL AND LENGTH(TRIM(full_text)) > 0"),
            ("detected_language_not_null",  "detected_language",  "detected_language IS NOT NULL AND LENGTH(TRIM(detected_language)) > 0"),
            ("transcription_model_not_null","transcription_model","transcription_model IS NOT NULL AND LENGTH(TRIM(transcription_model)) > 0"),
            ("duration_seconds_not_null",   "duration_seconds",   "duration_seconds IS NOT NULL AND duration_seconds >= 0"),
            ("accent_confidence_range",     "accent_confidence",  "accent_confidence IS NULL OR (accent_confidence >= 0.0 AND accent_confidence <= 1.0)"),
        ),
    ),

    "satisfaction_surveys": TableDefinition(
        table_name="satisfaction_surveys",
        primary_keys=["survey_id"],
        partition_column="process_date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=250_000,
        quality_rules=_rules(
            ("survey_id_not_null",      "survey_id",      "survey_id IS NOT NULL"),
            ("survey_date_not_null",    "survey_date",    "survey_date IS NOT NULL"),
            ("process_date_not_null",   "process_date",   "process_date IS NOT NULL"),
            ("customer_id_not_null",    "customer_id",    "customer_id IS NOT NULL"),
            ("survey_type_not_null",    "survey_type",    "survey_type IS NOT NULL AND LENGTH(TRIM(survey_type)) > 0"),
            ("send_channel_not_null",   "send_channel",   "send_channel IS NOT NULL AND LENGTH(TRIM(send_channel)) > 0"),
            ("main_score_not_null",     "main_score",     "main_score IS NOT NULL"),
            ("main_score_range",        "main_score",     "main_score >= 0 AND main_score <= 10"),
        ),
    ),

    "digital_events": TableDefinition(
        table_name="digital_events",
        primary_keys=["event_id"],
        partition_column="process_date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=10_000_000,
        quality_rules=_rules(
            ("event_id_not_null",       "event_id",       "event_id IS NOT NULL"),
            ("event_date_not_null",     "event_date",     "event_date IS NOT NULL"),
            ("process_date_not_null",   "process_date",   "process_date IS NOT NULL"),
            ("session_id_not_null",     "session_id",     "session_id IS NOT NULL AND LENGTH(TRIM(session_id)) > 0"),
            ("event_type_not_null",     "event_type",     "event_type IS NOT NULL AND LENGTH(TRIM(event_type)) > 0"),
            ("event_category_not_null", "event_category", "event_category IS NOT NULL AND LENGTH(TRIM(event_category)) > 0"),
            ("channel_not_null",        "channel",        "channel IS NOT NULL AND LENGTH(TRIM(channel)) > 0"),
            ("is_mobile_not_null",      "is_mobile",      "is_mobile IS NOT NULL"),
        ),
    ),

    "complaints": TableDefinition(
        table_name="complaints",
        primary_keys=["complaint_id"],
        partition_column="process_date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=80_000,
        quality_rules=_rules(
            ("complaint_id_not_null",         "complaint_id",         "complaint_id IS NOT NULL"),
            ("creation_date_not_null",        "creation_date",        "creation_date IS NOT NULL"),
            ("process_date_not_null",         "process_date",         "process_date IS NOT NULL"),
            ("customer_id_not_null",          "customer_id",          "customer_id IS NOT NULL"),
            ("case_type_not_null",            "case_type",            "case_type IS NOT NULL AND LENGTH(TRIM(case_type)) > 0"),
            ("category_not_null",             "category",             "category IS NOT NULL AND LENGTH(TRIM(category)) > 0"),
            ("reception_channel_not_null",    "reception_channel",    "reception_channel IS NOT NULL AND LENGTH(TRIM(reception_channel)) > 0"),
            ("description_not_null",          "description",          "description IS NOT NULL AND LENGTH(TRIM(description)) > 0"),
            ("priority_not_null",             "priority",             "priority IS NOT NULL AND LENGTH(TRIM(priority)) > 0"),
            ("status_not_null",               "status",               "status IS NOT NULL AND LENGTH(TRIM(status)) > 0"),
            ("sla_breached_not_null",         "sla_breached",         "sla_breached IS NOT NULL"),
            ("is_repeat_complainer_not_null", "is_repeat_complainer", "is_repeat_complainer IS NOT NULL"),
        ),
    ),

    "campaign_sends": TableDefinition(
        table_name="campaign_sends",
        primary_keys=["send_id"],
        partition_column="process_date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=2_000_000,
        quality_rules=_rules(
            ("send_id_not_null",        "send_id",        "send_id IS NOT NULL"),
            ("send_date_not_null",      "send_date",      "send_date IS NOT NULL"),
            ("process_date_not_null",   "process_date",   "process_date IS NOT NULL"),
            ("campaign_id_not_null",    "campaign_id",    "campaign_id IS NOT NULL"),
            ("customer_id_not_null",    "customer_id",    "customer_id IS NOT NULL"),
            ("send_channel_not_null",   "send_channel",   "send_channel IS NOT NULL AND LENGTH(TRIM(send_channel)) > 0"),
            ("send_status_not_null",    "send_status",    "send_status IS NOT NULL AND LENGTH(TRIM(send_status)) > 0"),
            ("was_delivered_not_null",  "was_delivered",  "was_delivered IS NOT NULL"),
            ("had_conversion_not_null", "had_conversion", "had_conversion IS NOT NULL"),
        ),
    ),

    # ── Reference table ──────────────────────────────────────────────────────

    "daily_exchange_rates": TableDefinition(
        table_name="daily_exchange_rates",
        # Composite PK: (date, source_currency, target_currency)
        primary_keys=["date", "source_currency", "target_currency"],
        partition_column="date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=3_000,
        quality_rules=_rules(
            ("date_not_null",            "date",            "date IS NOT NULL"),
            ("source_currency_not_null", "source_currency", "source_currency IS NOT NULL AND LENGTH(source_currency) = 3"),
            ("target_currency_not_null", "target_currency", "target_currency IS NOT NULL AND LENGTH(target_currency) = 3"),
            ("exchange_rate_not_null",   "exchange_rate",   "exchange_rate IS NOT NULL"),
            ("exchange_rate_positive",   "exchange_rate",   "exchange_rate > 0"),
        ),
    ),

    # ── Gold serving tables (pre-joined, query-optimized for dispute intake) ──

    "gold_dispute_customer_360": TableDefinition(
        table_name="gold_dispute_customer_360",
        primary_keys=["customer_id"],
        partition_column="snapshot_date",
        partition_strategy=PartitionStrategy.FULL_SNAPSHOT,
        approximate_rows=150_000,
        quality_rules=[],  # Gold tables enforce shape via build SQL, not Silver rules
    ),

    "gold_dispute_eligible_transactions": TableDefinition(
        table_name="gold_dispute_eligible_transactions",
        primary_keys=["transaction_id"],
        partition_column="transaction_date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=5_000_000,
        quality_rules=[],
    ),

    "gold_dispute_cases_summary": TableDefinition(
        table_name="gold_dispute_cases_summary",
        primary_keys=["complaint_id"],
        partition_column="creation_date",
        partition_strategy=PartitionStrategy.DAILY,
        approximate_rows=80_000,
        quality_rules=[],
    ),
}


# ---------------------------------------------------------------------------
# Public accessor
# ---------------------------------------------------------------------------


def get_table(table_name: str) -> TableDefinition:
    """
    Return the ``TableDefinition`` for *table_name*, raising ``KeyError`` with
    a helpful message listing valid names when the table is not registered.
    """
    if table_name not in TABLE_REGISTRY:
        valid = ", ".join(sorted(TABLE_REGISTRY))
        raise KeyError(
            f"Unknown table '{table_name}'. "
            f"Registered tables: {valid}"
        )
    return TABLE_REGISTRY[table_name]
