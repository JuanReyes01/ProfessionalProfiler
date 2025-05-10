# professional_profiler/scraping/wikipedia_search.py
from professional_profiler.logging.logger import get_logger

logger = get_logger(__name__)


def load_subject_list(path: str) -> list[str]:
    logger.debug("Loading subjects from %s", path)


def scrape_person(name: str, cfg):
    logger.debug("Scraping %r", name)
