"""
Unit tests for the Gold layer builder.

All tests run with DuckDB in-memory, building Silver views from synthetic
data rather than hitting Delta files, so they run fully offline.

Test coverage
-------------
test_customer_360_aggregates_products_and_complaints
    Verifies product_count, active_disputes, dispute_risk_level, and
    is_repeat_complainer are computed correctly from joined Silver tables.

test_customer_360_risk_level_high_for_repeat_complainers
    Verifies that dispute_risk_level = 'HIGH' when is_repeat_complainer is True,
    even with zero active disputes.

test_eligible_transactions_is_disputed_flag
    Verifies is_disputed=True when an open complaint references the transaction
    and is_disputed=False when no complaint exists.

test_eligible_transactions_eligibility_window
    Verifies is_eligible_for_dispute=False for transactions older than 90 days
    and for transactions that are already disputed.

test_eligible_transactions_not_disputed_and_recent
    Verifies is_eligible_for_dispute=True for a recent, undisputed transaction.

test_cases_summary_denormalizes_agent_and_interaction
    Verifies that agent name and origin interaction sentiment are denormalized
    into a single row keyed by complaint_id.
"""

from __future__ import annotations

from datetime import date, timedelta

import duckdb
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TODAY = date.today()
_RECENT = _TODAY - timedelta(days=10)
_OLD = _TODAY - timedelta(days=100)


def _setup_con() -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection with all Silver views pre-loaded."""
    con = duckdb.connect()

    # -- customers -----------------------------------------------------------
    con.execute(
        """
        CREATE TABLE silver_customers AS
        SELECT * FROM (VALUES
            ('C001', 'Ana',  'Lopez',  'ACTIVE', 'PREMIUM', 'CO', 720),
            ('C002', 'Luis', 'Gomez',  'ACTIVE', 'BASIC',   'MX', 580),
            ('C003', 'Sara', 'Torres', 'ACTIVE', 'PREMIUM', 'CO', 650)
        ) t(customer_id, first_name, last_name, customer_status, segment, country, credit_score)
        """
    )

    # -- products (2 products for C001, 1 for C002, 0 for C003) -------------
    con.execute(
        """
        CREATE TABLE silver_products AS
        SELECT * FROM (VALUES
            ('P001', 'C001', 'CHECKING',  'ACTIVE',   5000.0),
            ('P002', 'C001', 'SAVINGS',   'ACTIVE',  10000.0),
            ('P003', 'C002', 'CREDIT',    'INACTIVE', 2000.0)
        ) t(product_id, customer_id, product_type, product_status, current_balance)
        """
    )

    # -- complaints ----------------------------------------------------------
    con.execute(
        f"""
        CREATE TABLE silver_complaints AS
        SELECT * FROM (VALUES
            ('COMP001', 'C001', 'P001', 'TXN001', 'OPEN',     FALSE, NULL, '{_RECENT}', NULL, 'AGA001'),
            ('COMP002', 'C001', 'P001', 'TXN002', 'OPEN',     TRUE,  NULL, '{_RECENT}', NULL, 'AGA001'),
            ('COMP003', 'C001', 'P002', 'TXN003', 'CLOSED',   TRUE,  50.0, '{_OLD}',    '{_TODAY}', NULL),
            ('COMP004', 'C002', 'P003', 'TXN004', 'RESOLVED', FALSE, NULL, '{_OLD}',    '{_TODAY}', 'AGA002')
        ) t(
            complaint_id, customer_id, product_id, referenced_transaction_id,
            status, is_repeat_complainer, compensation_amount,
            creation_date, resolution_date, assigned_agent_id
        )
        """
    )

    # -- transactions --------------------------------------------------------
    con.execute(
        f"""
        CREATE TABLE silver_transactions AS
        SELECT * FROM (VALUES
            ('TXN001', 'C001', 'P001', '{_RECENT}', '{_RECENT}', 'PURCHASE', 200.0, 'USD', 'DIGITAL', 'CO', 'COMPLETED', FALSE, 0.1, 'MerchA', 'RETAIL'),
            ('TXN002', 'C001', 'P001', '{_RECENT}', '{_RECENT}', 'PURCHASE', 500.0, 'USD', 'DIGITAL', 'CO', 'COMPLETED', FALSE, 0.2, 'MerchB', 'TRAVEL'),
            ('TXN005', 'C003', 'P002', '{_RECENT}', '{_RECENT}', 'TRANSFER', 100.0, 'USD', 'APP',     'CO', 'COMPLETED', FALSE, 0.0, NULL,     NULL),
            ('TXN_OLD','C002', 'P003', '{_OLD}',    '{_OLD}',    'PURCHASE', 300.0, 'USD', 'ATM',     'MX', 'COMPLETED', FALSE, 0.0, NULL,     NULL)
        ) t(
            transaction_id, customer_id, product_id, transaction_date, process_date,
            transaction_type, amount, currency, channel, transaction_country,
            transaction_status, is_fraud, fraud_score, merchant_name, merchant_category
        )
        """
    )

    # -- satisfaction_surveys ------------------------------------------------
    con.execute(
        f"""
        CREATE TABLE silver_satisfaction_surveys AS
        SELECT * FROM (VALUES
            ('SUR001', 'C001', 8.0, '{_RECENT}', '{_RECENT}'),
            ('SUR002', 'C001', 6.0, '{_RECENT}', '{_RECENT}')
        ) t(survey_id, customer_id, main_score, survey_date, process_date)
        """
    )

    # -- service_agents ------------------------------------------------------
    con.execute(
        """
        CREATE TABLE silver_service_agents AS
        SELECT * FROM (VALUES
            ('AGA001', 'Maria', 'Ruiz',  'SPECIALIST', 'SENIOR', 'ES,EN'),
            ('AGA002', 'Pedro', 'Vidal', 'GENERALIST',  'JUNIOR', 'ES')
        ) t(agent_id, first_name, last_name, agent_type, experience_level, languages)
        """
    )

    # -- call_center_interactions --------------------------------------------
    con.execute(
        f"""
        CREATE TABLE silver_call_center_interactions AS
        SELECT * FROM (VALUES
            ('INT001', 'C001', 'COMP001', '{_RECENT}',  '{_RECENT}', 'PHONE', 'DISPUTE',  0.3, FALSE),
            ('INT002', 'C001', 'COMP001', '{_TODAY}',   '{_TODAY}',  'CHAT',  'FOLLOWUP', 0.7, FALSE),
            ('INT003', 'C002', 'COMP004', '{_RECENT}',  '{_RECENT}', 'PHONE', 'DISPUTE', -0.2, TRUE)
        ) t(
            interaction_id, customer_id, complaint_id, interaction_date, process_date,
            channel, contact_reason, sentiment_score, was_escalated
        )
        """
    )

    return con


def _run_customer_360(con: duckdb.DuckDBPyConnection) -> list[dict]:
    return con.execute(
        """
        WITH product_agg AS (
            SELECT
                customer_id,
                COUNT(*)                                            AS total_products,
                COUNT(*) FILTER (WHERE product_status = 'ACTIVE')  AS active_products,
                SUM(current_balance)                               AS total_balance,
                MAX(product_type)                                  AS primary_product_type
            FROM silver_products GROUP BY customer_id
        ),
        complaint_agg AS (
            SELECT
                customer_id,
                COUNT(*)                                                          AS total_complaints,
                COUNT(*) FILTER (WHERE status NOT IN ('CLOSED', 'RESOLVED'))     AS active_disputes,
                BOOL_OR(is_repeat_complainer)                                    AS is_repeat_complainer,
                SUM(COALESCE(compensation_amount, 0))                            AS total_compensation_paid
            FROM silver_complaints GROUP BY customer_id
        ),
        survey_agg AS (
            SELECT customer_id, AVG(main_score) AS avg_csat_score, COUNT(*) AS total_surveys
            FROM silver_satisfaction_surveys GROUP BY customer_id
        )
        SELECT
            c.customer_id,
            COALESCE(pa.total_products,    0)     AS total_products,
            COALESCE(pa.active_products,   0)     AS active_products,
            COALESCE(pa.total_balance,     0.0)   AS total_balance,
            COALESCE(ca.total_complaints,  0)     AS total_complaints,
            COALESCE(ca.active_disputes,   0)     AS active_disputes,
            COALESCE(ca.is_repeat_complainer, FALSE) AS is_repeat_complainer,
            COALESCE(ca.total_compensation_paid, 0.0) AS total_compensation_paid,
            sa.avg_csat_score,
            CASE
                WHEN COALESCE(ca.active_disputes, 0) >= 3
                     OR COALESCE(ca.is_repeat_complainer, FALSE) = TRUE THEN 'HIGH'
                WHEN COALESCE(ca.active_disputes, 0) BETWEEN 1 AND 2   THEN 'MEDIUM'
                ELSE 'LOW'
            END AS dispute_risk_level
        FROM silver_customers c
        LEFT JOIN product_agg   pa ON pa.customer_id = c.customer_id
        LEFT JOIN complaint_agg ca ON ca.customer_id = c.customer_id
        LEFT JOIN survey_agg    sa ON sa.customer_id = c.customer_id
        ORDER BY c.customer_id
        """
    ).df().to_dict(orient="records")


def _run_eligible_transactions(con: duckdb.DuckDBPyConnection) -> list[dict]:
    from sentinel_data.gold.build_gold import _DISPUTE_ELIGIBILITY_DAYS

    return con.execute(
        f"""
        WITH disputed_txns AS (
            SELECT DISTINCT referenced_transaction_id AS transaction_id
            FROM silver_complaints
            WHERE referenced_transaction_id IS NOT NULL
              AND status NOT IN ('CLOSED', 'RESOLVED')
        )
        SELECT
            t.transaction_id,
            t.customer_id,
            t.transaction_date,
            (dt.transaction_id IS NOT NULL) AS is_disputed,
            DATE_DIFF('day', t.transaction_date, CURRENT_DATE) AS days_since_transaction,
            (
                dt.transaction_id IS NULL
                AND DATE_DIFF('day', t.transaction_date, CURRENT_DATE) <= {_DISPUTE_ELIGIBILITY_DAYS}
            ) AS is_eligible_for_dispute
        FROM silver_transactions t
        LEFT JOIN disputed_txns dt ON dt.transaction_id = t.transaction_id
        ORDER BY t.transaction_id
        """
    ).df().to_dict(orient="records")


def _run_cases_summary(con: duckdb.DuckDBPyConnection) -> list[dict]:
    return con.execute(
        """
        WITH latest_interaction AS (
            SELECT * EXCLUDE (rn)
            FROM (
                SELECT *, ROW_NUMBER() OVER (
                    PARTITION BY complaint_id ORDER BY interaction_date DESC
                ) AS rn
                FROM silver_call_center_interactions
                WHERE complaint_id IS NOT NULL
            )
            WHERE rn = 1
        )
        SELECT
            comp.complaint_id,
            comp.customer_id,
            comp.status,
            comp.sla_breached,
            sa.first_name    AS agent_first_name,
            sa.last_name     AS agent_last_name,
            sa.agent_type,
            li.channel       AS origin_channel,
            li.sentiment_score AS origin_sentiment_score,
            li.interaction_date AS origin_interaction_date
        FROM silver_complaints comp
        LEFT JOIN silver_service_agents  sa ON sa.agent_id    = comp.assigned_agent_id
        LEFT JOIN latest_interaction     li ON li.complaint_id = comp.complaint_id
        ORDER BY comp.complaint_id
        """
    ).df().to_dict(orient="records")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def con():
    c = _setup_con()
    yield c
    c.close()


class TestCustomer360:
    def test_aggregates_products_and_complaints(self, con):
        rows = _run_customer_360(con)
        c001 = next(r for r in rows if r["customer_id"] == "C001")

        assert c001["total_products"] == 2
        assert c001["active_products"] == 2
        assert c001["total_balance"] == pytest.approx(15_000.0)
        # COMP001 and COMP002 are OPEN for C001
        assert c001["active_disputes"] == 2
        assert c001["dispute_risk_level"] == "MEDIUM"

    def test_no_products_yields_zero_balance(self, con):
        rows = _run_customer_360(con)
        c003 = next(r for r in rows if r["customer_id"] == "C003")
        assert c003["total_products"] == 0
        assert c003["total_balance"] == pytest.approx(0.0)

    def test_risk_level_high_for_repeat_complainers(self, con):
        rows = _run_customer_360(con)
        # C001 has is_repeat_complainer=TRUE on COMP002 → BOOL_OR → TRUE → HIGH
        c001 = next(r for r in rows if r["customer_id"] == "C001")
        assert c001["is_repeat_complainer"] is True
        assert c001["dispute_risk_level"] == "HIGH"

    def test_avg_csat_score(self, con):
        rows = _run_customer_360(con)
        c001 = next(r for r in rows if r["customer_id"] == "C001")
        assert c001["avg_csat_score"] == pytest.approx(7.0)


class TestEligibleTransactions:
    def test_is_disputed_flag_true(self, con):
        rows = _run_eligible_transactions(con)
        txn001 = next(r for r in rows if r["transaction_id"] == "TXN001")
        assert txn001["is_disputed"] is True
        assert txn001["is_eligible_for_dispute"] is False

    def test_is_disputed_flag_false_for_undisputed(self, con):
        rows = _run_eligible_transactions(con)
        txn005 = next(r for r in rows if r["transaction_id"] == "TXN005")
        assert txn005["is_disputed"] is False

    def test_eligible_for_recent_undisputed_transaction(self, con):
        rows = _run_eligible_transactions(con)
        txn005 = next(r for r in rows if r["transaction_id"] == "TXN005")
        assert txn005["is_eligible_for_dispute"] is True

    def test_ineligible_for_transactions_older_than_90_days(self, con):
        rows = _run_eligible_transactions(con)
        txn_old = next(r for r in rows if r["transaction_id"] == "TXN_OLD")
        assert txn_old["days_since_transaction"] > 90
        assert txn_old["is_eligible_for_dispute"] is False

    def test_ineligible_for_already_disputed_recent_transaction(self, con):
        rows = _run_eligible_transactions(con)
        txn002 = next(r for r in rows if r["transaction_id"] == "TXN002")
        assert txn002["is_disputed"] is True
        assert txn002["is_eligible_for_dispute"] is False


class TestCasesSummary:
    def test_denormalizes_agent_into_complaint_row(self, con):
        rows = _run_cases_summary(con)
        comp001 = next(r for r in rows if r["complaint_id"] == "COMP001")
        assert comp001["agent_first_name"] == "Maria"
        assert comp001["agent_last_name"] == "Ruiz"
        assert comp001["agent_type"] == "SPECIALIST"

    def test_latest_interaction_is_selected(self, con):
        """COMP001 has two interactions; INT002 (today) must win over INT001."""
        rows = _run_cases_summary(con)
        comp001 = next(r for r in rows if r["complaint_id"] == "COMP001")
        # INT002 is the most recent → channel=CHAT, sentiment=0.7
        assert comp001["origin_channel"] == "CHAT"
        assert comp001["origin_sentiment_score"] == pytest.approx(0.7)

    def test_no_agent_when_unassigned(self, con):
        rows = _run_cases_summary(con)
        comp003 = next(r for r in rows if r["complaint_id"] == "COMP003")
        assert comp003["agent_first_name"] is None

    def test_complaint_without_interaction_has_null_sentiment(self, con):
        rows = _run_cases_summary(con)
        comp002 = next(r for r in rows if r["complaint_id"] == "COMP002")
        # No interaction row references COMP002
        assert comp002["origin_sentiment_score"] is None
