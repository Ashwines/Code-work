"""Master pipeline orchestrator.

Runs the full ETL sequence: Staging → ODS → EDW → Data Marts.

Usage:
    python -m src.pipelines.run_pipeline
"""
import sys
import traceback
from pathlib import Path

# Ensure the BFSI root is on sys.path so `src` is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.logger import setup_logger
from src.config import load_config  # noqa: E402

logger = setup_logger("bfsi_pipeline", log_file="pipeline.log")

PIPELINE_STEPS = [
    ("staging", "staging_pipeline", "run_staging"),
    ("ods",     "ods_pipeline",    "run_ods"),
    # ("edw",     "edw_pipeline",    "run_edw"),
    # ("marts",   "mart_pipeline",   "run_marts"),
]


def main():
    """Execute every pipeline step in order."""
    cfg = load_config()
    logger.info("Starting BFSI ETL pipeline — project: %s", cfg["project"]["name"])

    for label, module_name, func_name in PIPELINE_STEPS:
        logger.info("=== Layer: %s (src.pipelines.%s) ===", label.upper(), module_name)
        try:
            mod = __import__(f"src.pipelines.{module_name}", fromlist=[func_name])
            func = getattr(mod, func_name)
            func()
            logger.info("Layer %s completed successfully.\n", label.upper())
        except Exception:
            logger.error("Layer %s failed with error:", label)
            logger.error(traceback.format_exc())
            sys.exit(1)

    logger.info("All layers completed. Pipeline finished successfully.")


if __name__ == "__main__":
    main()
