"""Data quality validators for the BFSI pipeline."""
import pandas as pd


def check_nulls(df: pd.DataFrame, required_cols: list) -> list:
    """Return list of columns that contain unexpected nulls."""
    issues = []
    for col in required_cols:
        if col in df.columns and df[col].isnull().any():
            count = int(df[col].isnull().sum())
            issues.append(f"{col}: {count} nulls")
    return issues


def check_duplicates(df: pd.DataFrame, key_cols: list) -> int:
    """Return count of duplicate rows based on key columns."""
    if not key_cols:
        return 0
    return int(df.duplicated(subset=key_cols, keep=False).sum())


def check_schema(df: pd.DataFrame, expected_cols: list) -> bool:
    """Verify that expected columns are present."""
    return set(expected_cols).issubset(set(df.columns))


def check_row_count(df: pd.DataFrame, min_rows: int = 1) -> bool:
    """Ensure the dataframe has at least ``min_rows`` rows."""
    return len(df) >= min_rows
