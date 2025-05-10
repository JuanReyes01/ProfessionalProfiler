"""
    This module is the entry point for the wikipedia 'scraping' (I'm using the API) application.

    TODO: create controller main function to handle the scraping process.
"""

# ===== IMPORTS =====

import sys
from professional_profiler.logging.logger import setup_logging, get_logger

# ===== FUNCTIONS =====


# ===== MAIN =====
def main():
    setup_logging()

    logger = get_logger(__name__)
    logger.info("Starting scraping stage")
    # cfg = load_app_config()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger = get_logger(__name__)
        logger.exception("Fatal error in scraping")
        sys.exit(1)
