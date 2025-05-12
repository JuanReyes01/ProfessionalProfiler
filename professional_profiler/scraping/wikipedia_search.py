# professional_profiler/scraping/wikipedia_search.py
from professional_profiler.logging.logger import get_logger
import os
import requests
from dotenv import load_dotenv
import time
from rapidfuzz import process, fuzz

load_dotenv()

logger = get_logger(__name__)


def get_wikipedia(
    name: str, lang: str = "en", retry: int = 3, timeout: int = 60, rc: int = 429
) -> str:
    logger.debug("Scraping %r", name)
    BASE_URL = "https://api.wikimedia.org/core/v1/wikipedia"
    HEADERS = {"Authorization": os.getenv("WP_ACCESS_TOKEN", "")}
    SEARCH_TIMEOUT = 5

    url = f"{BASE_URL}/{lang}/search/page"
    params = {"q": name, "limit": 1}
    rs = None
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

    # detection of disambiguation remains the same for the first result
    if pages[0].get("description") == "Topics referred to by the same term":
        return "MULTIPLE_MATCHES"

    # normalize query
    normalized_query = (
        name.lower().replace(" ", "_").replace(".", "")  # strip dots from initials/suffixes
    )

    # build candidate list from all returned pages
    choices = [p["key"].lower().replace(" ", "_") for p in pages]

    # fuzzy‐match
    best, score, idx = process.extractOne(normalized_query, choices, scorer=fuzz.ratio)

    if score < 50:
        return "NO_MATCH"

    # we accept pages[idx]
    match = pages[idx]

    return match["key"]


def search_html(
    key: str, lang: str = "en", retry: int = 3, timeout: int = 60, rc: int = 429
) -> str:
    logger.debug("Fetching %r", key)
    if key != "NO_MATCH" and key != "MULTIPLE_MATCHES" and key != "NO_RESULTS":
        url = "https://api.wikimedia.org/core/v1/wikipedia/" + lang + "/page/" + key + "/html"
        HEADERS = {
            "Authorization": os.getenv("WP_ACCESS_TOKEN"),
        }
        SEARCH_TIMEOUT = 5
        rs = None
        try:
            # Retry logic
            for attempt in range(retry):
                try:
                    rs = requests.get(url, headers=HEADERS, timeout=SEARCH_TIMEOUT)
                    rs.raise_for_status()
                    break
                except requests.HTTPError as e:
                    if rs.status_code == rc and attempt < retry - 1:
                        logger.warning(
                            "Rate limit hit, retrying... (%d/%d)", attempt + 1, retry
                        )
                        # Wait before retrying
                        logger.debug("Waiting for %d seconds before retrying...", timeout)
                        time.sleep(timeout)
                        continue
                    else:
                        raise e
            data = rs.text
        except requests.HTTPError:
            logger.error("HTTP error: %s", rs.status_code)
            return "HTTP error"
        except requests.RequestException:
            logger.error("Network error: %s", rs.status_code)
            return "Network error"
        return data
    else:
        return key
