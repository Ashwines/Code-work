"""Layer 4 transforms — EDW → Data Marts.

Builds subject-area fact tables with enrichment and derived metrics.
"""
import pandas as pd


def build_fact_transactions(ods_transactions: pd.DataFrame) -> pd.DataFrame:
    """Build ``trans_mart.fact_transactions``.

    Adds ``transaction_flag`` based on amount:
    - 'LARGE'  if Amount >= 10000
    - 'SMALL'  otherwise
    """
    df = ods_transactions.copy()
    df["transaction_flag"] = df["Amount"].apply(
        lambda x: "LARGE" if x >= 10000 else "SMALL"
    )
    return df[[
        "AccountID", "Amount", "Currency", "Description", "EventTs", "Status",
        "Suspicious", "TransactionDate", "TransactionFee", "TransactionID",
        "TransactionType", "load_dt", "load_ts", "transaction_flag",
    ]]


def build_fact_payments(ods_payments: pd.DataFrame) -> pd.DataFrame:
    """Build ``payment_mart.fact_payments``.

    Adds ``AmountInBaseCurrency = Amount * ExchangeRate``.
    """
    df = ods_payments.copy()
    df["AmountInBaseCurrency"] = df["Amount"] * df["ExchangeRate"]
    return df[[
        "Amount", "AuditTrial", "ClearingSystem", "Currency", "CustomerSegment",
        "Description", "ExchangeRate", "Fee", "FromAccountID", "MerchantName",
        "PaymentDate", "PaymentID", "PaymentType", "ToAccountID",
        "load_dt", "load_ts", "AmountInBaseCurrency",
    ]]


def build_fact_creditcard(ods_creditcard: pd.DataFrame,
                          ods_cust_profile: pd.DataFrame,
                          ods_loans: pd.DataFrame,
                          ods_employees: pd.DataFrame) -> pd.DataFrame:
    """Build ``cc_mart.fact_creditcard``.

    Enriches credit-card data with customer demographics and computes
    ``utilization_percent = Balance / CreditLimit * 100``.
    """
    df = ods_creditcard[["CustomerID", "CardID", "CardType", "Balance",
                         "CreditLimit", "BillCycle", "IssueDate",
                         "load_dt", "load_ts"]].copy()

    # Bring in customer name and phone
    cust = ods_cust_profile[["CustomerID", "FirstName", "PhoneNumber"]].copy()
    df = df.merge(cust, on="CustomerID", how="left")

    df["utilization_percent"] = (df["Balance"] / df["CreditLimit"] * 100).round(2)

    return df[[
        "customerid", "loanid", "employeeid", "firstname", "phonenumber",
        "cardid", "cardtype", "balance", "creditlimit", "billcycle",
        "issuedate", "utilization_percent", "load_dt", "load_ts",
    ]]


__all__ = [
    "build_fact_transactions",
    "build_fact_payments",
    "build_fact_creditcard",
]