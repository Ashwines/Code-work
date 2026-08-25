"""Layer 3 transforms — ODS → EDW.

Builds conformed dimensions and the ``fact_loans`` fact table.
"""
import pandas as pd


def build_customer_dim(ods_cust: pd.DataFrame) -> pd.DataFrame:
    """Build ``dim_customers`` from ``ods_cust_profile``.

    Columns: CustomerID, FirstName, LastName, Email, PhoneNumber,
    Address, DateOfBirth, BranchID, load_dt, load_ts, effective_date
    """
    return ods_cust[[
        "CustomerID", "FirstName", "LastName", "Email", "PhoneNumber",
        "Address", "DateOfBirth", "BranchID", "load_dt", "load_ts",
    ]].assign(effective_date=pd.to_datetime(ods_cust["load_dt"]))


def build_branch_dim(ods_branches: pd.DataFrame) -> pd.DataFrame:
    """Build ``dim_branches`` with SCD Type-2 columns.

    Columns: Address, BranchID, BranchName, City, State, Zipcode,
    load_dt, load_ts, start_date, end_date, is_current
    """
    df = ods_branches[[
        "Address", "BranchID", "BranchName", "City", "State", "Zipcode",
        "load_dt", "load_ts",
    ]].copy()
    df["start_date"] = df["load_dt"]
    df["end_date"] = None
    df["is_current"] = 1
    return df


def build_employee_dim(ods_employees: pd.DataFrame) -> pd.DataFrame:
    """Build ``dim_employees`` from ``ods_employees``."""
    return ods_employees[[
        "BranchID", "EmployeeID", "FirstName", "Hiredate",
        "LastName", "ManagerID", "Position", "load_dt", "load_ts",
    ]]


def build_loan_dim(ods_loans: pd.DataFrame) -> pd.DataFrame:
    """Build ``dim_loans`` from ``ods_loans``."""
    return ods_loans[[
        "Amount", "Collateral", "CustomerID", "EndDate", "InterestRate",
        "LoanID", "LoanType", "PaymentFrequency", "StartDate", "Status",
        "load_dt", "load_ts",
    ]]


def build_fact_loans(ods_loans: pd.DataFrame, ods_branches: pd.DataFrame) -> pd.DataFrame:
    """Build the ``fact_loans`` fact table with derived columns.

    Derived columns:
    - ``LoanDurationMonths``  — months between StartDate and EndDate
    - ``RiskIndicator``       — 'HIGH' / 'MEDIUM' / 'LOW' based on InterestRate
    - ``HighValueFlag``       — 'Y' if Amount >= 100_000 else 'N'
    - ``OutstandingBalance``  — current balance (approx: Amount * (1 + InterestRate/100))
    """
    import numpy as np

    df = ods_loans.copy()
    start = pd.to_datetime(df["StartDate"])
    end = pd.to_datetime(df["EndDate"])
    df["LoanDurationMonths"] = ((end - start).dt.days / 30.44).round().astype(int)

    df["RiskIndicator"] = pd.cut(
        df["InterestRate"],
        bins=[-np.inf, 5, 10, np.inf],
        labels=["LOW", "MEDIUM", "HIGH"],
    )

    df["HighValueFlag"] = np.where(df["Amount"] >= 100_000, "Y", "N")
    df["OutstandingBalance"] = df["Amount"] * (1 + df["InterestRate"] / 100)

    return df[[
        "LoanID", "CustomerID", "BranchID", "Amount", "InterestRate",
        "StartDate", "EndDate", "PaymentFrequency", "Status",
        "OutstandingBalance", "LoanDurationMonths", "RiskIndicator",
        "HighValueFlag", "load_dt", "load_ts",
    ]]


__all__ = [
    "build_customer_dim",
    "build_branch_dim",
    "build_employee_dim",
    "build_loan_dim",
    "build_fact_loans",
]