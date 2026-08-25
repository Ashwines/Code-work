"""Layer 2 — ODS (Operational Data Store) ingestion.

Loads data from staging tables into ODS tables using SQL INSERT...SELECT
statements.  Each ODS table is an exact copy of its staging counterpart
plus ``load_dt`` and ``load_ts`` audit columns.  Light data cleansing
(trim, upper-case, substring) is applied where noted.

Usage:
    python -m src.pipelines.ods_pipeline
"""
from sqlalchemy import text

from src.config import load_config
from src.database import get_engine, init_database
from src.utils.logger import setup_logger

logger = setup_logger("ods_pipeline", log_file="ods.log")

# ─── ODS SQL: Staging → ODS ──────────────────────────────────────────────
# Each statement reads from stgdb_ashwines.stg_* and writes to
# odsdb_ashwines.ods_* with load_dt / load_ts audit columns.
#
# Comments in the original:
#   "-- ODS loads from staging with exact copy"
#   "-- ODS Load from Staging with load_dt and load_ts"

ODS_INSERT_SQL = [
    # stg_accounts → ods_accounts
    # trim() on AccountType, upper() on Currency, filter nulls
    """
    INSERT INTO odsdb_ashwines.ods_accounts
    SELECT AccountID,
           TRIM(AccountType)     AS AccountType,
           Balance,
           CreditScore,
           UPPER(Currency)       AS Currency,
           CustomerID,
           DateOpened,
           ManagerID,
           ODLimit,
           CURRENT_DATE         AS load_dt,
           CURRENT_TIMESTAMP    AS load_ts
    FROM stgdb_ashwines.stg_accounts
    WHERE AccountID IS NOT NULL;
    """,
    # stg_transactions → ods_transactions (exact copy + audit cols)
    """
    INSERT INTO odsdb_ashwines.ods_transactions
    SELECT t.*,
           CURRENT_DATE    AS load_dt,
           CURRENT_TIMESTAMP AS load_ts
    FROM stgdb_ashwines.stg_transactions t;
    """,
    # stg_payments → ods_payments (exact copy + audit cols)
    """
    INSERT INTO odsdb_ashwines.ods_payments
    SELECT p.*,
           CURRENT_DATE    AS load_dt,
           CURRENT_TIMESTAMP AS load_ts
    FROM stgdb_ashwines.stg_payments p;
    """,
    # stg_creditcard → ods_creditcard (exact copy + audit cols)
    """
    INSERT INTO odsdb_ashwines.ods_creditcard
    SELECT c.*,
           CURRENT_DATE    AS load_dt,
           CURRENT_TIMESTAMP AS load_ts
    FROM stgdb_ashwines.stg_creditcard c;
    """,
    # stg_loans → ods_loans (exact copy + audit cols)
    """
    INSERT INTO odsdb_ashwines.ods_loans
    SELECT l.*,
           CURRENT_DATE    AS load_dt,
           CURRENT_TIMESTAMP AS load_ts
    FROM stgdb_ashwines.stg_loans l;
    """,
    # stg_cust_profile → ods_cust_profile
    # trim() on FirstName/LastName, substr() on PhoneNumber
    """
    INSERT INTO odsdb_ashwines.ods_cust_profile
    SELECT Address,
           BranchID,
           CustomerID,
           DateOfBirth,
           Email,
           TRIM(FirstName)       AS FirstName,
           TRIM(LastName)        AS LastName,
           SUBSTR(PhoneNumber, 1, 20) AS PhoneNumber,
           CURRENT_DATE         AS load_dt,
           CURRENT_TIMESTAMP    AS load_ts
    FROM stgdb_ashwines.stg_cust_profile cp;
    """,
    # stg_branches → ods_branches (exact copy + audit cols)
    """
    INSERT INTO odsdb_ashwines.ods_branches
    SELECT b.*,
           CURRENT_DATE    AS load_dt,
           CURRENT_TIMESTAMP AS load_ts
    FROM stgdb_ashwines.stg_branches b;
    """,
    # stg_employees → ods_employees (exact copy + audit cols)
    """
    INSERT INTO odsdb_ashwines.ods_employees
    SELECT e.*,
           CURRENT_DATE    AS load_dt,
           CURRENT_TIMESTAMP AS load_ts
    FROM stgdb_ashwines.stg_employees e;
    """,
]


def run_ods():
    """Staging → ODS: execute INSERT...SELECT statements."""
    cfg = load_config("database")
    db_type = cfg.get("default_db", "sqlite")

    # For cross-database queries in MySQL, we connect without a
    # specific database and let the SQL reference db.table directly.
    engine = get_engine(db_type, database="ods")
    # init_database(engine)

    logger.info("Starting ODS ingestion from staging")

    with engine.begin() as conn:
        for i, sql in enumerate(ODS_INSERT_SQL, 1):
            conn.execute(text(sql))
            logger.info("  -> ODS INSERT #%d executed", i)

    logger.info("ODS ingestion complete — 8 tables loaded")


if __name__ == "__main__":
    run_ods()

