# professional_profiler/scraping/wikipedia_search.py
from professional_profiler.logging.logger import get_logger
import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()

logger = get_logger(__name__)


def getWikipedia(
    name: str, lang: str = "en", retry: int = 3, timeout: int = 60, rc: int = 429
) -> str:
    logger.debug("Scraping %r", name)
    BASE_URL = "https://api.wikimedia.org/core/v1/wikipedia"
    HEADERS = {"Authorization": os.getenv("WP_ACCESS_TOKEN", "")}
    SEARCH_TIMEOUT = 5

    url = f"{BASE_URL}/{lang}/search/page"
    params = {"q": name, "limit": 1}

    try:
        # Retry logic
        for attempt in range(retry):
            try:
                rs = requests.get(url, headers=HEADERS, params=params, timeout=SEARCH_TIMEOUT)
                rs.raise_for_status()
                break
            except requests.HTTPError as e:
                if rs.status_code == rc and attempt < retry - 1:
                    logger.warning("Rate limit hit, retrying... (%d/%d)", attempt + 1, retry)
                    # Wait before retrying
                    logger.debug("Waiting for %d seconds before retrying...", timeout)
                    time.sleep(timeout)
                    continue
                else:
                    raise e
        data = rs.json()
    except requests.HTTPError:
        logger.error("HTTP error: %s", rs.status_code)
        return "HTTP error"
    except requests.RequestException:
        logger.error("Network error: %s", rs.status_code)
        return "Network error"
    except ValueError:
        logger.error("Invalid JSON response")
        return "Invalid JSON"

    pages = data.get("pages", [])
    if not pages:
        return "NO_RESULTS"

    page = pages[0]
    key = page.get("key", "")
    desc = page.get("description", "")

    # Disambiguation detection
    if desc == "Topics referred to by the same term":
        return "MULTIPLE_MATCHES"

    # Exact-match detection
    normalized_key = key.lower().replace(" ", "_")
    normalized_query = name.lower().replace(" ", "_")
    if normalized_key != normalized_query:
        return "NO_MATCH"
    article_url = "https://" + lang + ".wikipedia.org/wiki/" + page["key"]
    # Fallback to whatever description we got (or a default)
    return article_url or "NO_ARTICLE"
