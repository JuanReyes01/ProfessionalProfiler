# professional_profiler/modeling/model.py

from professional_profiler.logging.logger import get_logger, setup_logging
from professional_profiler.logging.config import load_config

# Initialize first thing in main
setup_logging()
logger = get_logger(__name__)
config = load_config()

# Example usage
logger.info("Initializing crawler with timeout=%s", config.crawler["request_timeout"])

try:
    print(22 + 1 + "")
except Exception as e:
    logger.error("Degree parsing failed for %s - %s", "A", str(e), exc_info=True)
