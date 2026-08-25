"""Layer 2 transforms — Staging → ODS.

Adds load metadata columns and performs light enrichment
before writing to ODS tables.
"""
from datetime import datetime

import pandas as pd


def add_load_metadata(df: pd.DataFrame, load_date: str = None) -> pd.DataFrame:
    """Add ``load_dt`` (DATE) and ``load_ts`` (TIMESTAMP) columns.

    Parameters
    ----------
    df : DataFrame
    load_date : str, optional
        Date string (YYYY-MM-DD). Defaults to today.
    """
    today = load_date or datetime.now().strftime("%Y-%m-%d")
    now = datetime.now()

    df = df.copy()
    df["load_dt"] = today
    df["load_ts"] = now
    return df


def staging_to_ods_table_map() -> dict:
    """Map staging table names to their ODS counterparts."""
    return {
        "stg_accounts":      "ods_accounts",
        "stg_transactions":  "ods_transactions",
        "stg_payments":      "ods_payments",
        "stg_creditcard":    "ods_creditcard",
        "stg_loans":         "ods_loans",
        "stg_cust_profile":  "ods_cust_profile",
        "stg_branches":      "ods_branches",
        "stg_employees":     "ods_employees",
    }


__all__ = ["add_load_metadata", "staging_to_ods_table_map"]