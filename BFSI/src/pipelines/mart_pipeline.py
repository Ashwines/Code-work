"""Layer 4 — Data Marts ingestion.

Builds subject-area fact / aggregate tables across the four data marts
(trans, payment, credit-card and loans marts) from ODS/EDW tables.
Each INSERT is preceded by a DELETE so the mart tables are idempotent
(re-loadable without duplicate rows).

Subject areas:
    * Loans mart        — fact_high_value_loans (with LoanCategory derivation)
    * Transaction mart  — fact_transactions (with transaction_flag)
    * Transaction mart  — agg_branch_trans_summary (branch aggregation)
    * Payment mart      — fact_payments (with AmountInBaseCurrency)
    * Credit-card mart  — fact_creditcard (with utilization percent)

Usage:
    python -m src.pipelines.mart_pipeline
"""
from sqlalchemy import text

from src.config import load_config
from src.database import get_engine, init_database
from src.utils.logger import setup_logger

logger = setup_logger("mart_pipeline", log_file="marts.log")


# ─── Mart SQL: ODS/EDW → Data Marts ───────────────────────────────────────
# Each mart INSERT is preceded by a DELETE to keep the load idempotent.
MART_INSERT_SQL = [
    # ── Loans mart: fact_high_value_loans with LoanCategory ────────────────
    "TRUNCATE TABLE loans_mart_ashwines.fact_high_value_loans",
    """
    INSERT INTO loans_mart_ashwines.fact_high_value_loans (
        LoanID,
        CustomerID,
        BranchID,
        Amount,
        InterestRate,
        StartDate,
        EndDate,
        PaymentFrequency,
        Status,
        OutstandingBalance,
        LoanDurationMonths,
        RiskIndicator,
        HighValueFlag,
        LoanCategory,
        load_dt,
        load_ts
    )
    SELECT
        LoanID,
        CustomerID,
        BranchID,
        Amount,
        InterestRate,
        StartDate,
        EndDate,
        PaymentFrequency,
        Status,
        OutstandingBalance,
        LoanDurationMonths,
        RiskIndicator,
        HighValueFlag,
        CASE
            WHEN RiskIndicator = 'HIGH'
                THEN 'HIGH_VALUE_HIGH_RISK'
            WHEN RiskIndicator = 'MEDIUM'
                THEN 'HIGH_VALUE_MEDIUM_RISK'
            ELSE 'HIGH_VALUE_LOW_RISK'
        END AS LoanCategory,
        CURRENT_DATE,
        CURRENT_TIMESTAMP
    FROM edwdb_ashwines.fact_loans
    WHERE HighValueFlag = 'Y';
    """,
    # ── Transaction MART: fact_transactions with transaction_flag ─────────
    "TRUNCATE TABLE trans_mart_ashwines.fact_transactions",
    """
    INSERT INTO trans_mart_ashwines.fact_transactions (
        AccountID,
        Amount,
        Currency,
        Description,
        EventTs,
        Status,
        Suspicious,
        TransactionDate,
        TransactionFee,
        TransactionID,
        TransactionType,
        transaction_flag
    )
    SELECT
        AccountID,
        Amount,
        Currency,
        Description,
        EventTs,
        Status,
        Suspicious,
        TransactionDate,
        TransactionFee,
        TransactionID,
        TransactionType,
        CASE WHEN Suspicious THEN 'FLAGGED' ELSE 'NORMAL' END
    FROM odsdb_ashwines.ods_transactions;
    """,
    # ── Transaction MART: branch-level aggregation ─────────────────────────
    "TRUNCATE TABLE trans_mart_ashwines.agg_branch_trans_summary",
    """
    INSERT INTO trans_mart_ashwines.agg_branch_trans_summary
    SELECT
        b.BranchID,
        b.BranchName,
        COUNT(DISTINCT c.CustomerID) AS Total_Customers,
        COUNT(DISTINCT a.AccountID)   AS Total_Accounts,
        SUM(a.Balance)                AS Total_Balance,
        SUM(t.Amount)                 AS Total_Transactions,
        CURRENT_DATE,
        CURRENT_TIMESTAMP
    FROM edwdb_ashwines.dim_branches b
    LEFT JOIN edwdb_ashwines.dim_customers c ON c.BranchID = b.BranchID
    LEFT JOIN odsdb_ashwines.ods_accounts a  ON a.CustomerID = c.CustomerID
    LEFT JOIN trans_mart_ashwines.fact_transactions t ON t.AccountID = a.AccountID
    GROUP BY b.BranchID, b.BranchName;
    """,



# ── Payment MART: fact_payments with AmountInBaseCurrency ──────────────
    "TRUNCATE TABLE payment_mart_ashwines.fact_payments",
    """
    INSERT INTO payment_mart_ashwines.fact_payments (
        Amount,
        AuditTrial,
        ClearingSystem,
        Currency,
        CustomerSegment,
        Description,
        ExchangeRate,
        Fee,
        FromAccountID,
        MerchantName,
        PaymentDate,
        PaymentID,
        PaymentType,
        ToAccountID,
        AmountInBaseCurrency,
        load_dt,
        load_ts
    )
    SELECT
        Amount,
        AuditTrial,
        ClearingSystem,
        Currency,
        CustomerSegment,
        Description,
        ExchangeRate,
        Fee,
        FromAccountID,
        MerchantName,
        PaymentDate,
        PaymentID,
        PaymentType,
        ToAccountID,
        CAST(Amount * ExchangeRate AS decimal(18,2)) AS AmountInBaseCurrency,
        CURRENT_DATE,
        CURRENT_TIMESTAMP
    FROM odsdb_ashwines.ods_payments;
    """,
    # ── Credit-card MART: fact_creditcard with utilization percent ────────
    "TRUNCATE TABLE cc_mart_ashwines.fact_creditcard",
    """
    INSERT INTO cc_mart_ashwines.fact_creditcard (
        customerid,
        loanid,
        employeeid,
        firstname,
        phonenumber,
        cardid,
        cardtype,
        balance,
        creditlimit,
        billcycle,
        issuedate,
        utilization_percent,
        load_dt,
        load_ts
    )
    SELECT
        oc.customerid,
        NULL AS loanid,
        NULL AS employeeid,
        dcu.firstname,
        dcu.phonenumber,
        oc.cardid,
        oc.cardtype,
        oc.balance,
        oc.creditlimit,
        oc.billcycle,
        oc.issuedate,
        CASE
            WHEN oc.creditlimit IS NULL
                 OR oc.creditlimit = 0
            THEN NULL
            ELSE ROUND(
                (oc.balance / oc.creditlimit) * 100, 2)
        END AS utilization_percent,
        oc.load_dt,
        oc.load_ts
    FROM odsdb_ashwines.ods_creditcard oc
    LEFT JOIN edwdb_ashwines.dim_customers dcu
        ON oc.customerid = dcu.customerid
    WHERE oc.load_dt = (
        SELECT MAX(load_dt)
        FROM odsdb_ashwines.ods_creditcard);
    """,
]
def run_marts():
    """EDW → Data Marts: fact_transactions, fact_payments, fact_creditcard."""
    cfg = load_config("database")
    db_type = cfg.get("default_db", "sqlite")
    engine = get_engine(db_type, database="trans_mart")
    # init_database(engine)

    logger.info("Starting data marts ingestion")

    with engine.begin() as conn:
        for i, sql in enumerate(MART_INSERT_SQL, 1):
            conn.execute(text(sql))
            logger.info("  -> Mart step #%d executed", i)

    logger.info("Data marts ingestion complete — all marts rebuilt")


if __name__ == "__main__":
    run_marts()
