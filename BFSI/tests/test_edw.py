"""Tests for EDW-layer transforms."""
import pandas as pd

from src.transforms.edw_transforms import (
    build_customer_dim,
    build_branch_dim,
    build_employee_dim,
    build_loan_dim,
    build_fact_loans,
)


class TestBuildCustomerDim:
    def test_selects_correct_columns(self):
        df = pd.DataFrame({
            "Address": ["Addr1"],
            "BranchID": ["B001"],
            "CustomerID": ["C001"],
            "DateOfBirth": ["1990-01-01"],
            "Email": ["a@b.com"],
            "FirstName": ["John"],
            "LastName": ["Doe"],
            "PhoneNumber": ["555-0101"],
            "load_dt": ["2024-01-01"],
            "load_ts": ["2024-01-01 00:00:00"],
        })
        result = build_customer_dim(df)
        assert "effective_date" in result.columns
        assert "CustomerID" in result.columns


class TestBuildBranchDim:
    def test_adds_scd2_columns(self):
        df = pd.DataFrame({
            "Address": ["Addr"],
            "BranchID": ["B001"],
            "BranchName": ["Downtown"],
            "City": ["NYC"],
            "State": ["NY"],
            "Zipcode": ["10001"],
            "load_dt": ["2024-01-01"],
            "load_ts": ["2024-01-01 00:00:00"],
        })
        result = build_branch_dim(df)
        assert "start_date" in result.columns
        assert "end_date" in result.columns
        assert "is_current" in result.columns
        assert result["is_current"].iloc[0] == 1


class TestBuildFactLoans:
    def test_calculates_derived_columns(self):
        df = pd.DataFrame({
            "Amount": [150000, 5000],
            "Collateral": ["House", "None"],
            "CustomerID": ["C001", "C002"],
            "EndDate": ["2028-01-01", "2026-01-01"],
            "InterestRate": [12.5, 5.0],
            "LoanID": ["L001", "L002"],
            "LoanType": ["Mortgage", "Personal"],
            "PaymentFrequency": ["Monthly", "Annual"],
            "StartDate": ["2023-01-01", "2023-01-01"],
            "Status": ["Active", "Closed"],
            "BranchID": ["B001", "B002"],
            "load_dt": ["2024-01-01", "2024-01-01"],
            "load_ts": ["2024-01-01 00:00:00", "2024-01-01 00:00:00"],
        })
        result = build_fact_loans(df, pd.DataFrame())
        assert "LoanDurationMonths" in result.columns
        assert "RiskIndicator" in result.columns
        assert "HighValueFlag" in result.columns
        assert "OutstandingBalance" in result.columns
        # High-value flag
        assert result["HighValueFlag"].tolist() == ["Y", "N"]
