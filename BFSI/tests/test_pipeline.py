"""Integration tests for the overall pipeline orchestration."""
import pytest

from src.utils.validators import (
    check_nulls,
    check_duplicates,
    check_schema,
    check_row_count,
)


class TestValidators:
    def test_check_nulls(self):
        import pandas as pd
        df = pd.DataFrame({"A": [1, None, 3], "B": [1, 2, 3]})
        issues = check_nulls(df, ["A", "B"])
        assert "A: 1 nulls" in issues

    def test_check_duplicates(self):
        import pandas as pd
        df = pd.DataFrame({"ID": [1, 1, 2], "Val": ["a", "b", "c"]})
        assert check_duplicates(df, ["ID"]) == 2

    def test_check_schema(self):
        import pandas as pd
        df = pd.DataFrame({"A": [1], "B": [2]})
        assert check_schema(df, ["A", "B"]) is True
        assert check_schema(df, ["A", "C"]) is False

    def test_check_row_count(self):
        import pandas as pd
        df = pd.DataFrame({"A": [1, 2, 3]})
        assert check_row_count(df, min_rows=1) is True
        assert check_row_count(df, min_rows=5) is False


class TestPipelineStructure:
    def test_config_loads(self):
        from src.config import load_config
        cfg = load_config()
        assert "project" in cfg
        assert "sources" in cfg
        assert len(cfg["sources"]) == 8

    def test_pipeline_steps_exist(self):
        from src.pipelines.run_pipeline import PIPELINE_STEPS
        assert len(PIPELINE_STEPS) == 4
        labels = [s[0] for s in PIPELINE_STEPS]
        assert labels == ["staging", "ods", "edw", "marts"]
