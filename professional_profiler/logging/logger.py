# logger.py
import logging
from logging.handlers import RotatingFileHandler
import yaml
from pathlib import Path


def setup_logging(config_path: str = "config.yaml") -> None:
    """Initialize logging configuration"""

    # Create logs directory
    logs_dir = Path("./data/logs")
    logs_dir.mkdir(exist_ok=True)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    logging_config = config["logging"]

    # Base configuration
    logging.basicConfig(
        level=logging_config["level"],
        format=logging_config["format"],
        handlers=[
            RotatingFileHandler(
                filename=logging_config["file_path"],
                maxBytes=logging_config["max_size"],
                backupCount=logging_config["backup_count"],
            ),
            logging.StreamHandler(),
        ],
    )

    # Silence noisy libraries
    for logger in ["urllib3", "asyncio"]:
        logging.getLogger(logger).setLevel(logging.WARNING)


def get_logger(name: str = None) -> logging.Logger:
    """Get configured logger instance"""
    return logging.getLogger(name or __name__)
