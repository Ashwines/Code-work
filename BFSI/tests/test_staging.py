"""Tests for staging-layer transforms."""
import pandas as pd

from src.transforms.staging_transforms import (
    strip_whitespace,
    fix_null_strings,
    standardize_columns,
    reorder_columns,
    STAGING_COLUMNS,
)


class TestStripWhitespace:
    def test_strips_string_columns(self):
        df = pd.DataFrame({"Name": ["  Alice  ", " Bob "], "Val": [1, 2]})
        result = strip_whitespace(df)
        assert result["Name"].tolist() == ["Alice", "Bob"]


class TestFixNullStrings:
    def test_replaces_null_strings_with_none(self):
        df = pd.DataFrame({"Col": ["null", "NULL", "valid", "nan"]})
        result = fix_null_strings(df)
        assert result["Col"].tolist() == [None, None, "valid", None]


class TestStandardizeColumns:
    def test_fixes_suspecious_typo(self):
        df = pd.DataFrame({"Suspecious": [True, False]})
        result = standardize_columns(df)
        assert "Suspicious" in result.columns
        assert "Suspecious" not in result.columns


class TestReorderColumns:
    def test_reorders_to_match_schema(self):
        df = pd.DataFrame({
            "DateOpened": ["2022-01-01"],
            "AccountID": ["A001"],
            "Balance": [1000.0],
        })
        result = reorder_columns(df, "stg_accounts")
        assert result.columns[0] == "AccountID"

    def test_unknown_table_returns_unchanged(self):
        df = pd.DataFrame({"X": [1]})
        result = reorder_columns(df, "nonexistent_table")
        assert list(result.columns) == ["X"]
