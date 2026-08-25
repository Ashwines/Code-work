"""Layer 4 — Data Marts ingestion.

Builds subject-area fact tables from the EDW.

Usage:
    python -m src.pipelines.mart_pipeline
"""
from src.config import load_config
from src.database import get_engine
from src.utils.logger import setup_logger

logger = setup_logger("mart_pipeline", log_file="marts.log")


def run_marts():
    """EDW → Data Marts: fact_transactions, fact_payments, fact_creditcard."""
    cfg = load_config()
    engine = get_engine("sqlite")
    logger.info("Starting data marts ingestion")

    # --- TODO: implement mart transforms ---
    # from src.transforms.mart_transforms import build_fact_transactions
    # from src.transforms.mart_transforms import build_fact_payments
    # from src.transforms.mart_transforms import build_fact_creditcard

    logger.info("Data marts ingestion skeleton — see src.transforms.mart_transforms")


if __name__ == "__main__":
    run_marts()
