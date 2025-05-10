# professional_profiler/logging/logger.py
import logging.config
from pathlib import Path
import yaml

LOGGING_CONFIG = Path(__file__).parent.parent.parent / "config" / "logging.yaml"


def setup_logging(config_path: str | Path = LOGGING_CONFIG) -> None:
    """
    Reads a dictConfig‐style YAML and configures logging once.
    """
    try:
        cfg = yaml.safe_load(Path(config_path).read_text())
        logging.config.dictConfig(cfg)
    except Exception as e:
        # fallback to a minimal console logger
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        logging.getLogger(__name__).warning(
            "[CRITICAL] Could not load logging config %s: %s", config_path, e
        )


def get_logger(name: str = None):
    """
    Return a standard library Logger(name). Assumes setup_logging() has run.
    """
    return logging.getLogger(name or __name__)
