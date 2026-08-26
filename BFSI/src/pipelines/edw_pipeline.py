"""Layer 3 - EDW (Enterprise Data Warehouse) ingestion.

Builds conformed dimensions (SCD Type 1 & Type 2) and fact tables
from the ODS layer using a MySQL stored procedure defined in
``src/transforms/sp_edw_transforms.sql``.

The procedure encapsulates all INSERT/UPDATE/TRUNCATE statements,
so MySQL parses the semicolons inside BEGIN...END as internal
statement terminators rather than separate network round-trips.

Usage:
    python -m src.pipelines.edw_pipeline
"""
from pathlib import Path

from sqlalchemy import text

from src.config import load_config
from src.database import get_engine, init_database
from src.utils.logger import setup_logger

logger = setup_logger("edw_pipeline", log_file="edw.log")

# Location of the stored-procedure SQL file (relative to this module).
SQL_FILE = Path(__file__).resolve().parent.parent / "transforms" / "sp_edw_transforms.sql"

DROP_PROCEDURE_SQL = "DROP PROCEDURE IF EXISTS sp_edw_load"
CALL_PROCEDURE_SQL = "CALL sp_edw_load()"


def run_edw():
    """ODS -> EDW: build dimensions and fact tables via stored procedure."""
    cfg = load_config("database")
    engine = get_engine(cfg.get("default_db", "sqlite"), database="staging")

    # init_database(engine)

    logger.info("Reading stored procedure from %s", SQL_FILE)
    with open(SQL_FILE, "r", encoding="utf-8") as fh:
        create_proc_sql = fh.read()

    logger.info("Starting EDW ingestion from ODS")

    with engine.begin() as conn:
        conn.execute(text(DROP_PROCEDURE_SQL))
        conn.execute(text(create_proc_sql))
        conn.execute(text(CALL_PROCEDURE_SQL))
        logger.info("  -> sp_edw_load dropped, created, and called")

    logger.info("EDW ingestion complete -- all dimensions and facts loaded")


if __name__ == "__main__":
    run_edw()
