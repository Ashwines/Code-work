"""Shared pytest fixtures for the BFSI test suite."""
import os
import sys
import tempfile

import pytest
from sqlalchemy import create_engine, text

# Ensure src is importable
BFSI_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BFSI_ROOT, "src"))

from src.config import PROJECT_ROOT  # noqa: E402


@pytest.fixture
def raw_data_dir():
    """Path to the raw CSV directory."""
    return PROJECT_ROOT / "data" / "raw"


@pytest.fixture
def sample_db(tmp_path):
    """Provide a temporary in-memory SQLite database for tests."""
    db_path = tmp_path / "test_bfsi.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    yield engine
    engine.dispose()


@pytest.fixture
def staging_df():
    """A small sample DataFrame simulating raw accounts CSV data."""
    import pandas as pd

    return pd.DataFrame({
        "AccountID": ["A001", "A002", "A003"],
        "AccountType": ["Savings", "Checking", "Business"],
        "Balance": [5000.00, 12000.50, 87500.00],
        "CreditScore": [720, 680, 750],
        "Currency": ["USD", "USD", "USD"],
        "CustomerID": ["C001", "C002", "C003"],
        "DateOpened": ["2022-01-15", "2021-06-30", "2023-03-10"],
        "ManagerID": ["M01", "M02", "M01"],
        "ODLimit": [0.0, 5000.0, 25000.0],
    })
