"""Configuration loader for the BFSI data engineering project."""
import os
from pathlib import Path

import yaml

# Project root is two levels up from this file (src/config.py -> BFSI/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def load_config(name: str = "config") -> dict:
    """Load a YAML configuration file from the config/ directory."""
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT
