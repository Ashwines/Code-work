"""Layer 1 — Staging ingestion.

Reads raw CSV files from ``data/raw/`` and loads each into a staging
table in the target database (MySQL in production, SQLite for local dev).

Usage:
    python -m src.pipelines.staging_pipeline
"""
import pandas as pd

from src.config import load_config, PROJECT_ROOT
from src.database import get_engine, init_database
from src.utils.logger import setup_logger

logger = setup_logger("staging_pipeline", log_file="staging.log")


def run_staging():
    """Load raw CSVs → staging tables."""
    cfg = load_config("database")
    engine = get_engine(cfg.get("default_db", "sqlite"), database="staging")
    # init_database(engine)

    folder = str(PROJECT_ROOT / "data" / "raw")
    import os
    folder = os.path.join(folder, "")  # ensure trailing separator

    table_file_dict = {
        "stg_transactions": folder + "transactions.csv",
        "stg_accounts":     folder + "accounts.csv",
        "stg_payments":     folder + "payments.csv",
        "stg_creditcard":   folder + "creditcard.csv",
        "stg_loans":        folder + "loans.csv",
        "stg_cust_profile": folder + "cust.csv",
        "stg_branches":     folder + "branches.csv",
        "stg_employees":    folder + "employee.csv",
    }

    logger.info("Reading raw CSVs from %s", folder)

    # ─── Loop & Load ─────────────────────────────────────────────────────
    #   Each iteration: reads CSV → loads to the staging table (replace if exists)
    for table, file in table_file_dict.items():
        df = pd.read_csv(file)

        # Optional: filter/transform before loading
        # e.g. df = df.query("BranchID == 130")

        df.to_sql(table, con=engine, index=False, if_exists="replace")
        logger.info("  -> %s: %d rows loaded into %s", file, len(df), table)

    logger.info("Staging ingestion complete — 8 tables loaded")


if __name__ == "__main__":
    run_staging()
