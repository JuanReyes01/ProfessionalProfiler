"""
    This module is the entry point for the wikipedia 'scraping' (I'm using the API) application.

    TODO: create controller main function to handle the scraping process.
"""

# ===== IMPORTS =====

import sys
from professional_profiler.logging.logger import setup_logging, get_logger
from professional_profiler.config import load_app_config
from professional_profiler.scraping.wikipedia_search import getWikipedia
import pandas as pd

setup_logging()
conf = load_app_config()
logger = get_logger(__name__)

# ===== FUNCTIONS =====


def load_subject_list(path: str) -> list[str]:
    logger.debug("Loading subjects from %s", path)
    # import and create a list of subjects
    try:
        subjects = pd.read_csv(path, header=None)[0].tolist()
        logger.debug("Loaded %d subjects", len(subjects))
        return subjects
    except FileNotFoundError:
        logger.error("File not found: %s", path)
        return []
    except Exception as e:
        logger.error("Error loading subjects: %s", e)
        return []


# ===== MAIN =====
def main():

    logger.info("Starting wikipedia link gathering")
    # Load the subject list
    logger.debug("Loading subject list from %s", conf.scraping.paths.authors)
    subjects = load_subject_list(conf.scraping.paths.authors)
    if not subjects:
        logger.error("No subjects found in the file.")
        return
    logger.debug("Loaded %d subjects", len(subjects))
    # Process each subject
    for subject in subjects:
        logger.debug("Processing subject: %s", subject)
        # Call the Wikipedia API
        wiki_conf = conf.scraping.wikipedia
        result = getWikipedia(
            subject,
            lang=wiki_conf.language,
            retry=wiki_conf.max_retries,
            timeout=wiki_conf.timeout,
            rc=wiki_conf.response_code,
        )
        logger.info("Result for %s: %s", subject, result)
        # Save the result to a file or database
        # NOTE: This is not an efficient way to save the results,
        # but I want it to save partial results in case of an error
        with open(conf.scraping.paths.processed_data + conf.scraping.file.name, "a") as file:
            file.write(f"{subject}: {result}\n")
    logger.info("Finished processing subjects")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger = get_logger(__name__)
        logger.exception("Fatal error in scraping")
        sys.exit(1)
