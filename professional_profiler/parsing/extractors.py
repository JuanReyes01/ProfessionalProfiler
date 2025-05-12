from bs4 import BeautifulSoup, Tag, NavigableString
from nltk.tokenize import sent_tokenize
import re
from .utils import is_html
from .constants import DEGREE_PATTERN, LOOSE_DEGREE_RE, BLACKLIST_SECTIONS
from .formatter import degrees_to_markdown
from professional_profiler.logging.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def extract_all_sections(html: str) -> list[dict]:
    logger.info("Starting extraction of all sections from HTML.")
    soup = BeautifulSoup(html, "html5lib")

    # strip site-wide junk
    for sel in [
        "style",
        "script",
        "table.navbox",
        "sup.reference",
        "span.mw-cite-backlink",
        "ol.references",
        "div.reflist",
        "div.hatnote",
        "div#toc",
    ]:
        for el in soup.select(sel):
            logger.debug(f"Decomposing element: {sel}")
            el.decompose()

    body = soup.select_one("div.mw-parser-output") or soup
    sections = []

    # Lead paragraph(s)
    lead_chunks = []
    first_h = body.find(re.compile(r"^h[1-6]$"))
    for sib in body.children:
        if sib is first_h:
            break
        if isinstance(sib, Tag) and sib.name == "p":
            lead_chunks.append(sib.get_text(" ", strip=True))
    lead_text = " ".join(lead_chunks).strip()
    if lead_text:
        logger.debug("Extracted lead section text.")
        sections.append({"title": "_lead_", "content": lead_text})

    for h in body.find_all(re.compile(r"^h[1-6]$")):
        title = h.get_text(strip=True)
        if title in BLACKLIST_SECTIONS:
            logger.info(f"Skipping blacklisted section: {title}")
            continue
        content = extract_section_text(h)
        if content:
            logger.debug(f"Extracted section: {title}")
            sections.append({"title": title, "content": content})

    # Infobox education as a pseudo-section
    infobox = soup.find("table", class_="infobox")
    if infobox:
        edu_texts = []
        for row in infobox.find_all("tr"):
            hdr = row.find("th")
            cell = row.find("td")
            if (
                hdr
                and cell
                and (
                    "education" in hdr.get_text(" ", strip=True).lower()
                    or "alma mater" in hdr.get_text(" ", strip=True).lower()
                )
            ):
                edu_texts.append(cell.get_text(" ", strip=True))
        if edu_texts:
            logger.debug("Extracted education information from infobox.")
            sections.append({"title": "_infobox_education_", "content": "; ".join(edu_texts)})

    logger.info("Completed extraction of all sections.")
    return sections


# Heading-based sections
def extract_section_text(tag: Tag) -> str:
    logger.debug(f"Extracting text for section: {tag.get_text(strip=True)}")
    level = int(tag.name[1])
    texts = []
    for sib in tag.next_siblings:
        if isinstance(sib, Tag) and re.fullmatch(r"h[1-6]", sib.name):
            if int(sib.name[1]) <= level:
                break
        if isinstance(sib, Tag) and sib.name == "p":
            texts.append(sib.get_text(" ", strip=True))
        elif isinstance(sib, NavigableString) and sib.strip():
            texts.append(str(sib).strip())
    section_text = " ".join(texts).strip()
    if not section_text:
        logger.warning(f"No content found for section: {tag.get_text(strip=True)}")
    return section_text


def parse_degrees_from_sections(sections: list[dict]) -> dict:
    logger.info("Parsing degrees from sections.")
    extracted = {}
    for sec in sections:
        for sent in sent_tokenize(sec["content"]):
            if DEGREE_PATTERN.search(sent):
                logger.debug(
                    f"Degree mention found in section '{sec['title']}': {sent.strip()}"
                )
                extracted.setdefault(sec["title"], []).append(sent.strip())
    if not extracted:
        logger.warning("No degree mentions found in any section.")
    return extracted


def extract_every_degree_sentence(html: str) -> list[str]:
    logger.info("Extracting every degree-related sentence from HTML.")
    sections = extract_all_sections(html)
    hits = []
    for sec in sections:
        for sent in sent_tokenize(sec["content"]):
            if LOOSE_DEGREE_RE.search(sent):
                logger.debug(f"Loose degree mention found: {sent.strip()}")
                hits.append(sent.strip())
    if not hits:
        logger.warning("No loose degree mentions found.")
    return list(dict.fromkeys(hits))


def extract_degrees_markdown(html: str) -> str:
    logger.info("Extracting degrees and converting to markdown.")
    if not is_html(html):
        logger.debug("Input is not HTML, skipping parsing.")
        return "NOT HTML"
    sections = extract_all_sections(html)
    sec_map = parse_degrees_from_sections(sections)
    if sec_map:
        logger.info("Successfully parsed degrees from sections.")
        return degrees_to_markdown(sec_map)

    # fallback
    logger.warning("No structured degree mentions found, falling back to loose mentions.")
    fallback = extract_every_degree_sentence(html)
    md = "## Degree Mentions\n" + "\n".join(f"- {s}" for s in fallback)
    return md
