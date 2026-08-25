"""Layer 3 — EDW (Enterprise Data Warehouse) ingestion.

Builds conformed dimensions and the loans fact table from ODS.

Usage:
    python -m src.pipelines.edw_pipeline
"""
from src.config import load_config
from src.database import get_engine
from src.utils.logger import setup_logger

logger = setup_logger("edw_pipeline", log_file="edw.log")


def run_edw():
    """ODS → EDW: dimensions + fact_loans."""
    cfg = load_config()
    engine = get_engine("sqlite")
    logger.info("Starting EDW ingestion")

    # --- TODO: implement EDW transforms ---
    # from src.transforms.edw_transforms import build_customer_dim, build_branch_dim
    # from src.transforms.edw_transforms import build_employee_dim, build_loan_dim
    # from src.transforms.edw_transforms import build_fact_loans

    logger.info("EDW ingestion skeleton — see src.transforms.edw_transforms")


if __name__ == "__main__":
    run_edw()
