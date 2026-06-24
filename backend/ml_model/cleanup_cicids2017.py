"""
Cleanup script - Remove all CICIDS2017 trained models and artifacts.

This script deletes:
  - All .pkl files from saved_models/ (models, scalers, encoders, etc.)
  - All report files from reports/

Usage:
    python ml_model/cleanup_cicids2017.py
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
REPORTS_DIR = BASE_DIR / "reports"


def cleanup():
    """Remove all CICIDS2017 artifacts."""
    log.info("Cleaning up CICIDS2017 artifacts...")

    # Delete all pickle files from saved_models
    if SAVED_MODELS_DIR.exists():
        pkl_files = list(SAVED_MODELS_DIR.glob("*.pkl"))
        if pkl_files:
            log.info(f"Deleting {len(pkl_files)} model/artifact files:")
            for f in pkl_files:
                log.info(f"  - {f.name}")
                f.unlink()
        else:
            log.info("No .pkl files found in saved_models/")
    else:
        log.info("saved_models/ directory does not exist")

    # Delete all report files from reports
    if REPORTS_DIR.exists():
        report_files = list(REPORTS_DIR.glob("*"))
        if report_files:
            log.info(f"Deleting {len(report_files)} report files:")
            for f in report_files:
                log.info(f"  - {f.name}")
                if f.is_file():
                    f.unlink()
        else:
            log.info("No report files found in reports/")
    else:
        log.info("reports/ directory does not exist")

    log.info("Cleanup complete.")


if __name__ == "__main__":
    cleanup()
