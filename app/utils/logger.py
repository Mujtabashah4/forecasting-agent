"""
Logging configuration
"""
import logging
import sys
from pathlib import Path
from app.config import settings


def setup_logger():
    """Setup application logger"""
    # Create logs directory if it doesn't exist
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


# Initialize logger
logger = setup_logger()
