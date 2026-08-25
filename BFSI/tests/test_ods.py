"""Tests for ODS-layer transforms."""
from src.transforms.ods_transforms import (
    add_load_metadata,
    staging_to_ods_table_map,
)


class TestAddLoadMetadata:
    def test_adds_load_dt_and_load_ts(self, staging_df):
        import pandas as pd
        result = add_load_metadata(staging_df)
        assert "load_dt" in result.columns
        assert "load_ts" in result.columns
        assert len(result) == len(staging_df)

    def test_custom_load_date(self, staging_df):
        result = add_load_metadata(staging_df, load_date="2024-01-15")
        assert (result["load_dt"] == "2024-01-15").all()


class TestStagingToOdsTableMap:
    def test_maps_all_tables(self):
        mapping = staging_to_ods_table_map()
        assert mapping["stg_accounts"] == "ods_accounts"
        assert mapping["stg_transactions"] == "ods_transactions"
        assert mapping["stg_loans"] == "ods_loans"
        assert len(mapping) == 8
