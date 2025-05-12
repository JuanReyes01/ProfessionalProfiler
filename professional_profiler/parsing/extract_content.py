import re
from bs4 import BeautifulSoup, NavigableString, Tag
import codecs
from professional_profiler.logging.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def load_html_from_df(source):
    if isinstance(source, str):
        html = codecs.decode(source, "unicode_escape")
        soup = BeautifulSoup(html, "html5lib")

    elif isinstance(source, bytes):
        pass
    else:
        raise ValueError("Invalid input type. Expected str or bytes.")
    return soup


def extract_infobox_education(soup):
    infobox = soup.find("table", class_="infobox")
    if not infobox:
        return None
    for row in infobox.find_all("tr"):
        header = row.find("th")
        cell = row.find("td")
        if header and cell and "education" in header.get_text(" ", strip=True).lower():
            return cell.get_text(" ", strip=True)
    return None


def extract_section_text(tag):
    level = int(tag.name[1])
    texts = []
    for sib in tag.next_siblings:
        if isinstance(sib, Tag) and re.fullmatch(r"h[1-6]", sib.name):
            if int(sib.name[1]) <= level:
                break
        if isinstance(sib, Tag):
            texts.append(sib.get_text(" ", strip=True))
        elif isinstance(sib, NavigableString) and sib.strip():
            texts.append(str(sib).strip())
    return " ".join(texts).strip()


def build_heading_tree_with_content(html):
    for bad in html.select("style, script, table.navbox"):
        bad.decompose()
    headings = html.find_all(re.compile(r"^h[1-6]$"))
    tree, stack = [], []
    for h in headings:
        node = {
            "level": int(h.name[1]),
            "title": h.get_text(strip=True),
            "id": h.get("id"),
            "content": extract_section_text(h),
            "children": [],
        }
        while stack and stack[-1]["level"] >= node["level"]:
            stack.pop()
        if stack:
            stack[-1]["children"].append(node)
        else:
            tree.append(node)
        stack.append(node)
    return tree


def search_keywords_in_tree(tree, keywords):
    matching_branches = []
    for branch in tree:
        for kw in keywords:
            if kw in branch["title"]:
                matching_branches.append(
                    {
                        "id": branch["id"],
                        "content": branch["content"],
                        "level": branch["level"],
                        "keyword": kw,
                    }
                )
                break
        if branch.get("children"):
            child_matches = search_keywords_in_tree(branch["children"], keywords)
            matching_branches.extend(child_matches)
    return matching_branches
