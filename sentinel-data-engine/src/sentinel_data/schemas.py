"""
Gold Layer Data Contracts – Pydantic schemas for dispute intake serving tables.

These models define the official data contract between the sentinel-data-engine
Gold layer and the FastAPI backend (sentinel-ai-core).  Any field added or
removed here must be reflected in both the build_gold.py SQL and the API layer.

Usage
-----
    from sentinel_data.schemas import (
        GoldDisputeCustomer360,
        GoldDisputeEligibleTransaction,
        GoldDisputeCasesSummary,
    )

    # Validate a row returned by DuckDB or Spark
    row = GoldDisputeCustomer360(**duckdb_row_dict)
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# gold_dispute_customer_360
# ---------------------------------------------------------------------------


class GoldDisputeCustomer360(BaseModel):
    """
    One row per customer_id.

    Pre-joins customers, products (aggregated), complaints (aggregated), and
    satisfaction surveys (average CSAT).  Consumed by the FastAPI /customer
    endpoint and LLM orchestrator tool calls that need full customer context
    without runtime join overhead.

    PII note
    --------
    ``customer_id`` is retained in this prototype to support sub-50 ms
    point-lookups with local DuckDB.  Production deployments must apply
    dynamic tokenization via Azure Key Vault before exposing this table
    outside the data platform boundary.  See ADR 023-pii-gold-handling.
    """

    # Identity
    customer_id: str = Field(..., description="Surrogate customer key (PII – see ADR 008)")
    first_name: str = Field(..., description="Customer given name (PII)")
    last_name: str = Field(..., description="Customer family name (PII)")
    document_type: str = Field(..., description="Identity document type (e.g. DNI, PASSPORT)")
    document_number: str = Field(..., description="Identity document number (PII)")
    date_of_birth: str = Field(..., description="Date of birth in ISO 8601 format (PII)")

    # Demographics
    city: str
    state: str
    country: str
    segment: str = Field(..., description="Customer segment (e.g. RETAIL, PREMIUM)")
    customer_status: str = Field(..., description="Account status (ACTIVE, INACTIVE, BLOCKED)")
    registration_date: str = Field(..., description="ISO 8601 date of first account opening")
    credit_score: Optional[float] = Field(None, ge=0, description="Credit bureau score")

    # Product aggregates
    total_products: int = Field(..., ge=0)
    active_products: int = Field(..., ge=0)
    total_balance: float = Field(..., description="Sum of current_balance across all products")
    primary_product_type: Optional[str] = None

    # Complaint aggregates
    total_complaints: int = Field(..., ge=0)
    active_disputes: int = Field(..., ge=0, description="Open/pending complaints")
    is_repeat_complainer: bool
    total_claimed_amount: float = Field(..., ge=0, description="Sum of claimed_amount across complaints")

    # Survey aggregates
    avg_csat_score: Optional[float] = Field(None, ge=0, le=10)
    total_surveys: int = Field(..., ge=0)

    # Derived risk
    dispute_risk_level: str = Field(
        ..., description="HIGH | MEDIUM | LOW – derived from active_disputes and repeat flag"
    )

    # Metadata
    snapshot_date: date = Field(..., description="Date when this Gold snapshot was built")


# ---------------------------------------------------------------------------
# gold_dispute_eligible_transactions
# ---------------------------------------------------------------------------


class GoldDisputeEligibleTransaction(BaseModel):
    """
    One row per transaction_id.

    Pre-joins transactions with customers and the complaints table.  Exposes
    boolean eligibility flags used by the dispute intake API to decide whether
    a customer may open a new dispute for a given transaction.

    Business rule
    -------------
    ``is_eligible_for_dispute`` is True when the transaction is NOT already
    under an open dispute AND ``days_since_transaction`` <= 90 (configurable
    via ``_DISPUTE_ELIGIBILITY_DAYS`` in build_gold.py).
    """

    # Transaction identity
    transaction_id: str = Field(..., description="Unique transaction key")
    transaction_date: str = Field(..., description="ISO 8601 posting date")
    process_date: str = Field(..., description="ISO 8601 processing / settlement date")
    product_id: str
    customer_id: str = Field(..., description="Owning customer key (PII – see ADR 008)")
    transaction_type: str
    amount: float = Field(..., description="Transaction amount in the original currency; enforced as DOUBLE at the SQL layer")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    channel: str
    transaction_country: str
    transaction_status: str
    is_fraud: bool
    fraud_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None

    # Customer context (denormalized)
    customer_first_name: str = Field(..., description="PII")
    customer_last_name: str = Field(..., description="PII")
    customer_segment: str
    customer_country: str
    customer_credit_score: Optional[float] = None

    # Eligibility flags
    is_disputed: bool = Field(..., description="True when an open complaint references this transaction")
    days_since_transaction: int = Field(..., ge=0)
    is_eligible_for_dispute: bool = Field(
        ...,
        description="True when NOT already disputed AND days_since_transaction <= 90",
    )

    # Metadata
    snapshot_date: date


# ---------------------------------------------------------------------------
# v_service_dispute_eligible_transactions  (PII-free service projection)
# ---------------------------------------------------------------------------


class ServiceDisputeEligibleTransaction(BaseModel):
    """
    PII-free projection of gold_dispute_eligible_transactions.

    Exposed to the FastAPI backend and any downstream service that does NOT
    hold explicit PII-READ permission.  Drops the three PII columns mandated
    by ADR 008:
        - customer_first_name
        - customer_last_name
        - customer_credit_score

    All eligibility flags, transaction fields, and non-PII customer context
    (segment, country) are preserved.

    Source table
    ------------
    v_service_dispute_eligible_transactions (Delta table in local Gold dir or
    Unity Catalog gold schema in Databricks).
    """

    # Transaction identity
    transaction_id: str
    transaction_date: str
    process_date: str
    product_id: str
    customer_id: str = Field(..., description="Opaque token in production (see ADR 008)")
    transaction_type: str
    amount: float = Field(..., description="Transaction amount; always numeric (DOUBLE at SQL layer)")
    currency: str = Field(..., min_length=3, max_length=3)
    channel: str
    transaction_country: str
    transaction_status: str
    is_fraud: bool
    fraud_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None

    # Non-PII customer context
    customer_segment: str
    customer_country: str

    # Eligibility flags
    is_disputed: bool
    days_since_transaction: int = Field(..., ge=0)
    is_eligible_for_dispute: bool = Field(
        ...,
        description="True when NOT already disputed AND days_since_transaction <= 90",
    )

    # Metadata
    snapshot_date: date


# ---------------------------------------------------------------------------
# gold_dispute_cases_summary
# ---------------------------------------------------------------------------


class GoldDisputeCasesSummary(BaseModel):
    """
    One row per complaint_id.

    Denormalizes complaints with customers, products, service agents, and the
    most recent call-center interaction.  Consumed by the case-management
    dashboard and the LLM context builder that must explain an open dispute
    to an agent without issuing any runtime joins.
    """

    # Complaint core
    complaint_id: str = Field(..., description="Unique complaint / case key")
    creation_date: str = Field(..., description="ISO 8601 date the complaint was opened")
    resolution_date: Optional[str] = Field(None, description="ISO 8601 date closed; None if open")
    case_type: str
    category: str
    subcategory: Optional[str] = None
    reception_channel: str
    description: str
    priority: str = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL")
    status: str = Field(..., description="OPEN | IN_PROGRESS | RESOLVED | CLOSED")
    sla_breached: bool
    resolution_notes: Optional[str] = None
    claimed_amount: Optional[float] = Field(None, ge=0, description="Amount claimed by customer")
    compensation_granted: Optional[bool] = Field(None, description="Whether compensation was granted")
    is_repeat_complainer: bool

    # Customer context (denormalized)
    customer_id: str = Field(..., description="PII – see ADR 008")
    customer_first_name: str = Field(..., description="PII")
    customer_last_name: str = Field(..., description="PII")
    customer_segment: str
    customer_country: str
    customer_credit_score: Optional[float] = None

    # Product context (denormalized)
    product_id: Optional[str] = None
    product_type: Optional[str] = None
    product_number: Optional[str] = None
    product_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    product_balance: Optional[float] = None

    # Assigned agent context (denormalized)
    assigned_agent_id: Optional[str] = None
    agent_first_name: Optional[str] = None
    agent_last_name: Optional[str] = None
    agent_type: Optional[str] = None
    agent_experience_level: Optional[str] = None
    agent_languages: Optional[str] = None

    # Most recent call-center interaction (denormalized)
    origin_interaction_id: Optional[str] = None
    origin_interaction_date: Optional[str] = None
    origin_channel: Optional[str] = None
    origin_contact_reason: Optional[str] = None
    origin_sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    origin_was_escalated: Optional[bool] = None

    # Derived
    case_age_days: int = Field(..., ge=0, description="Days from creation_date to resolution or today")

    # Metadata
    snapshot_date: date
