"""Layer 1 transforms — Raw CSV → Staging.

Each function takes a raw ``pandas.DataFrame`` (as read from CSV)
and returns a cleaned DataFrame ready for loading into a staging table.
"""
import pandas as pd

# Canonical column-name mapping for the ``Suspecious`` → ``Suspicious`` typo
COLUMN_RENAME = {"Suspecious": "Suspicious"}

# Expected column order for each staging table (from DDL)
STAGING_COLUMNS = {
    "stg_accounts":  ["AccountID", "AccountType", "Balance", "CreditScore",
                      "Currency", "CustomerID", "DateOpened", "ManagerID", "ODLimit"],
    "stg_transactions": ["AccountID", "Amount", "Currency", "Description",
                         "EventTs", "Status", "Suspicious", "TransactionDate",
                         "TransactionFee", "TransactionID", "TransactionType"],
    "stg_payments":    ["Amount", "AuditTrial", "ClearingSystem", "Currency",
                        "CustomerSegment", "Description", "ExchangeRate", "Fee",
                        "FromAccountID", "MerchantName", "PaymentDate", "PaymentID",
                        "PaymentType", "ToAccountID"],
    "stg_creditcard":  ["Balance", "BillCycle", "CardID", "CardNumber", "CardType",
                        "CreditLimit", "CustomerID", "ExpirationDate", "InterestRate",
                        "IssueDate", "Status"],
    "stg_loans":       ["Amount", "Collateral", "CustomerID", "EndDate",
                        "InterestRate", "LoanID", "LoanType", "PaymentFrequency",
                        "StartDate", "Status"],
    "stg_cust_profile": ["Address", "BranchID", "CustomerID", "DateOfBirth",
                         "Email", "FirstName", "LastName", "PhoneNumber"],
    "stg_branches":    ["Address", "BranchID", "BranchName", "City", "State", "Zipcode"],
    "stg_employees":   ["BranchID", "EmployeeID", "FirstName", "Hiredate",
                        "LastName", "ManagerID", "Position"],
}


def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from all string columns."""
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def fix_null_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Replace literal 'null' / 'NULL' / 'nan' strings with actual None."""
    df = df.replace({"null": None, "NULL": None, "nan": None, "NaN": None})
    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Apply canonical column-name mappings (e.g. fix typos)."""
    return df.rename(columns=COLUMN_RENAME)


def reorder_columns(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Reorder DataFrame columns to match the staging table schema."""
    cols = STAGING_COLUMNS.get(table)
    if cols:
        df = df[[c for c in cols if c in df.columns]]
    return df


__all__ = [
    "strip_whitespace",
    "fix_null_strings",
    "standardize_columns",
    "reorder_columns",
    "STAGING_COLUMNS",
]